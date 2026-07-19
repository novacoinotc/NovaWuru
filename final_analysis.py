#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ANÁLISIS COMPLETO DE LA FINAL — todos los mercados en probabilidades.
Argentina vs España (Final Mundial 2026). Modelo full desde 0:
  1) Investigación profunda GLM: 22 gemelos (11v11) + entorno + estadísticas de equipo
     (córners, faltas, tarjetas, tiros) + árbitro.
  2) Monte Carlo 100k: goles + córners + tarjetas + faltas + goleadores + derivados.
Uso: python3 final_analysis.py
"""
import json, os, sys, time
import numpy as np
from collections import Counter
from multiprocessing import Pool, cpu_count
from concurrent.futures import ThreadPoolExecutor
from glm_research import glm, parse_json, research_match, USAGE
import sim_match as SM

ROOT = os.path.dirname(os.path.abspath(__file__))
META = {"id": "ARG_ESP", "home": "Argentina", "away": "Spain", "group": "FINAL",
        "venue": "MetLife Stadium, New Jersey", "host": ""}
CONSENSUS = 3      # cada dato se investiga 3 veces por GLM (independientes) -> mediana
SM.N = int(os.environ.get("SIM_N", 2_000_000))   # simulación MASIVA (20× lo normal) para la final

# ---------- 1) Investigación de estadísticas de equipo y árbitro ----------
def get_team_stats(team, opp):
    p = (f"Con WEB SEARCH, estadísticas REALES de {team} en el Mundial 2026 (y forma reciente) de cara a la final vs {opp}.\n"
         "Promedios por partido: córners a favor, córners en contra, faltas cometidas, tarjetas amarillas, "
         "tarjetas rojas (freq), tiros totales, tiros a puerta, posesión %.\n"
         'Responde SOLO JSON: {"corners_for":num,"corners_against":num,"fouls":num,"yellows":num,'
         '"reds_per_game":0-1,"shots":num,"shots_on_target":num,"possession":0-100}. Sin texto.')
    try:
        d = parse_json(glm(p, max_tokens=900))
        return d
    except Exception:
        return dict(corners_for=5.0, corners_against=4.5, fouls=12.0, yellows=2.0,
                    reds_per_game=0.06, shots=13.0, shots_on_target=4.5, possession=50)

def get_referee(home, away):
    p = (f"Con WEB SEARCH, ¿quién arbitra la FINAL del Mundial 2026 {home} vs {away}? "
         "Y su promedio de tarjetas por partido y tendencia (estricto/permisivo, penales).\n"
         'Responde SOLO JSON: {"name":"...","yellows_per_game":num,"reds_per_game":0-1,"strictness":0-100,"pen_tendency":0-100}. Sin texto.')
    try:
        return parse_json(glm(p, max_tokens=500))
    except Exception:
        return dict(name="(por confirmar)", yellows_per_game=4.2, reds_per_game=0.12, strictness=60, pen_tendency=50)

# defaults sensatos si GLM devuelve 0/None (evita romper los modelos)
DEF_STATS = dict(corners_for=5.0, corners_against=4.7, fouls=12.5, yellows=2.2,
                 reds_per_game=0.07, shots=13.5, shots_on_target=4.7, possession=50)
def san_stats(d):
    d = dict(d or {})
    for k, dv in DEF_STATS.items():
        v = d.get(k)
        try: v = float(v)
        except (TypeError, ValueError): v = 0.0
        d[k] = v if v > 0 else dv
    return d

# ---------- 2) Simulación de goles (reusa el motor) + mercados extra ----------
def sim_goals(M):
    AH = SM.arr(M['home']['players']); AA = SM.arr(M['away']['players'])
    bh = SM.base_idx(AH); ba = SM.base_idx(AA); env = M.get('env') or {}
    meta = M['meta']; hh = meta.get('host') == meta.get('home'); ha = meta.get('host') == meta.get('away')
    lamH, lamA = SM.elo_base_lams(meta['home'], meta['away'], hh, ha)
    cores = max(cpu_count() - 1, 1); chunk = SM.N // cores
    with Pool(cores) as pool:
        res = pool.map(SM.worker, [(AH, AA, env, hh, ha, chunk, 7 + i, bh, ba, lamH, lamA) for i in range(cores)])
    gm = np.concatenate([r[0] for r in res]); ga = np.concatenate([r[1] for r in res])
    return gm.astype(int), ga.astype(int), float(np.mean([r[2] for r in res])), float(np.mean([r[3] for r in res]))

def ou_lines(arr, lines):
    return {f"Over {l}": float(np.mean(arr > l)) for l in lines}

def main():
    t0 = time.time()
    print(f"⚽ ANÁLISIS COMPLETO — {META['home']} vs {META['away']} (Final Mundial 2026)\n{'='*64}")

    # ---- Investigación (deep, TODA con GLM; consenso de 3 pasadas por dato) ----
    mf = os.path.join(ROOT, f"match_{META['id']}.json")
    if os.path.exists(mf) and os.path.getsize(mf) > 64_000:
        print(f"🧠 Investigación 11v11 ya hecha a profundidad (reuso).")
    else:
        print(f"🧠 GLM investigando 11v11 + entorno (profundo, desde 0)...")
        research_match(META)  # crea match_ARG_ESP.json (22 gemelos + env)
    print(f"📊 GLM investigando stats de equipo + árbitro (consenso ×{CONSENSUS})...")
    def consensus(fn, *args):
        with ThreadPoolExecutor(CONSENSUS) as ex:
            outs = [f.result() for f in [ex.submit(fn, *args) for _ in range(CONSENSUS)]]
        keys = outs[0].keys()
        agg = {}
        for k in keys:
            vals = [o.get(k) for o in outs if o.get(k) is not None]
            nums = [float(v) for v in vals if isinstance(v, (int, float))]
            agg[k] = float(np.median(nums)) if nums else (vals[0] if vals else None)
        return agg
    with ThreadPoolExecutor(3) as ex:
        fH = ex.submit(consensus, get_team_stats, META['home'], META['away'])
        fA = ex.submit(consensus, get_team_stats, META['away'], META['home'])
        fR = ex.submit(consensus, get_referee, META['home'], META['away'])
        stH, stA, ref = san_stats(fH.result()), san_stats(fA.result()), (fR.result() or {})
    # override: árbitro REAL confirmado (investigado con Opus web) tiene prioridad sobre GLM
    ov = os.path.join(ROOT, 'referee_override.json')
    if os.path.exists(ov): ref = json.load(open(ov, encoding='utf-8'))
    ref_yc = float(ref.get('yellows_per_game') or 0) or 4.5   # si árbitro no anunciado: default final ~4.5
    print(f"   Stats ARG: córners {stH['corners_for']:.1f} | faltas {stH['fouls']:.1f} | amarillas {stH['yellows']:.1f} | tiros {stH['shots']:.1f}")
    print(f"   Stats ESP: córners {stA['corners_for']:.1f} | faltas {stA['fouls']:.1f} | amarillas {stA['yellows']:.1f} | tiros {stA['shots']:.1f}")
    print(f"   Árbitro: {ref.get('name') or '(por confirmar)'} (~{ref_yc:.1f} amarillas/partido)")

    M = json.load(open(mf, encoding='utf-8'))

    # ---- Simulación de goles ----
    print(f"🎲 Simulando {SM.N:,} partidos (goles)...")
    gm, ga, lh, la = sim_goals(M)
    n = len(gm); tot = gm + ga; diff = gm - ga
    rng = np.random.default_rng(2026)

    # ---- Córners: esperado = (corners_for propio + corners_against rival)/2, modulado por ataque de cada sim ----
    ecH = (float(stH['corners_for']) + float(stA['corners_against'])) / 2
    ecA = (float(stA['corners_for']) + float(stH['corners_against'])) / 2
    attH = np.clip(1 + 0.06 * (gm - gm.mean()), 0.7, 1.5)   # más goles ese sim ≈ más ataque ≈ más córners
    attA = np.clip(1 + 0.06 * (ga - ga.mean()), 0.7, 1.5)
    cornH = rng.poisson(np.clip(ecH * attH, 0.5, None)); cornA = rng.poisson(np.clip(ecA * attA, 0.5, None))
    corn = cornH + cornA

    # ---- Faltas ----
    efouls = float(stH['fouls']) + float(stA['fouls'])
    tension = 1 + 0.10 * (np.abs(diff) <= 1)   # partido cerrado = más roce; es final
    fouls = rng.poisson(np.clip(efouls * tension, 3, None))

    # ---- Tarjetas: mezcla base-equipos y árbitro + intensidad de final, correlada con faltas ----
    team_yc = float(stH['yellows']) + float(stA['yellows'])          # amarillas esperadas por rendimiento de equipos
    base_cards = 0.5 * team_yc + 0.5 * ref_yc                         # blend equipos/árbitro (ambos saneados)
    lam_cards = base_cards * 1.15 * (0.85 + 0.30 * (fouls / max(efouls, 1)))  # +15% final + roce del partido
    yellows = rng.poisson(np.clip(lam_cards, 1.5, None))
    p_red = np.clip(float(stH.get('reds_per_game', 0.07)) + float(stA.get('reds_per_game', 0.07)) + float(ref.get('reds_per_game') or 0.1), 0.03, 0.6)
    reds = (rng.random(n) < p_red).astype(int) + (rng.random(n) < p_red * 0.4).astype(int)
    booking_pts = yellows * 10 + reds * 25

    # ---- Tiros ----
    shotsH = rng.poisson(np.clip(float(stH['shots']) * attH, 1, None))
    shotsA = rng.poisson(np.clip(float(stA['shots']) * attA, 1, None))

    # ---- Goleadores: reparte goles por (peso ataque × finishing) ----
    def scorer_w(players):
        wa = np.array([SM.rw(p['position'])[0] for p in players])
        fin = np.array([float(p.get('finishing', 50)) for p in players])
        w = wa * (fin / 60.0) + 1e-6; return w / w.sum()
    wH = scorer_w(M['home']['players']); wA = scorer_w(M['away']['players'])
    expH = np.outer(wH, gm); expA = np.outer(wA, ga)      # goles esperados por jugador
    anyH = 1 - np.exp(-expH.mean(1)); anyA = 1 - np.exp(-expA.mean(1))   # anytime P(>=1)
    egH_pl = expH.mean(1); egA_pl = expA.mean(1)          # goles esperados por jugador
    # primer goleador ≈ P(hay gol) × P(su equipo marca primero) × cuota de anotación del jugador
    p_goal = np.mean(tot >= 1); shareH = lh / (lh + la); shareA = 1 - shareH
    firstH = p_goal * shareH * wH; firstA = p_goal * shareA * wA
    p_nogoal = float(np.mean(tot == 0))

    # ---- Tarjetas por jugador: reparte amarillas por (indisciplina × posición) ----
    def card_pos(pos):
        p = pos.lower()
        if any(k in p for k in ('portero', 'gk', 'arquero')): return 0.15
        if any(k in p for k in ('contenc', 'pivote', 'cdm', 'defensivo', 'volante de marca')): return 1.6
        if any(k in p for k in ('central', 'zaguero', 'cb', 'lateral', 'back', 'defensa')): return 1.3
        if any(k in p for k in ('extremo', 'winger', 'lw', 'rw', 'banda')): return 0.7
        if any(k in p for k in ('delantero', 'punta', 'striker', 'st', '9', 'centro')): return 0.7
        if any(k in p for k in ('mediapunta', 'enganche', '10', 'cam', 'ofensiv')): return 0.85
        return 1.1   # mediocampo
    def card_w(players):
        w = np.array([card_pos(p['position']) * (100 - float(p.get('discipline', 70))) / 50 + 0.05 for p in players])
        return w
    cwH = card_w(M['home']['players']); cwA = card_w(M['away']['players'])
    cw_all = np.concatenate([cwH, cwA]); cw_all = cw_all / cw_all.sum()
    exp_cards_pl = cw_all * yellows.mean()                # amarillas esperadas por jugador
    p_booked = 1 - np.exp(-exp_cards_pl)                  # P(ver amarilla)
    names_all = [p['name'] for p in M['home']['players']] + [p['name'] for p in M['away']['players']]
    teams_all = [META['home']] * 11 + [META['away']] * 11

    def pct(x): return f"{x*100:.1f}%"
    R = {}
    print(f"\n{'='*64}\n📈 RESULTADO ({SM.N:,} simulaciones) — {META['home']} vs {META['away']}\n{'='*64}")

    print(f"\n🥅 GOLES  (λ {lh:.2f}-{la:.2f})")
    hw, dr, aw = np.mean(gm > ga), np.mean(gm == ga), np.mean(gm < ga)
    print(f"  1X2:  {META['home']} {pct(hw)} | Empate {pct(dr)} | {META['away']} {pct(aw)}")
    print(f"  Doble oport: 1X {pct(hw+dr)} | 12 {pct(hw+aw)} | X2 {pct(dr+aw)}")
    print(f"  Goles esperados: {gm.mean():.2f}-{ga.mean():.2f} (total {tot.mean():.2f})")
    for k, v in ou_lines(tot, [1.5, 2.5, 3.5]).items(): print(f"  {k} goles: {pct(v)}  (Under {pct(1-v)})")
    print(f"  BTTS (ambos anotan): {pct(np.mean((gm>=1)&(ga>=1)))}")
    print(f"  Ambos equipos NO anotan: {pct(np.mean((gm==0)|(ga==0)))}")
    top = Counter(zip(gm.tolist(), ga.tolist())).most_common(6)
    print("  Marcadores exactos: " + " · ".join(f"{a}-{b} {c/n*100:.1f}%" for (a, b), c in top))
    print(f"  Margen: gana ARG por 2+ {pct(np.mean(diff>=2))} | por 1 {pct(np.mean(diff==1))} | ESP por 1 {pct(np.mean(diff==-1))} | ESP 2+ {pct(np.mean(diff<=-2))}")
    print(f"  Total par/impar: par {pct(np.mean(tot%2==0))} | impar {pct(np.mean(tot%2==1))}")

    print(f"\n🚩 CÓRNERS  (esp {ecH:.1f}-{ecA:.1f}, total {corn.mean():.1f})")
    for k, v in ou_lines(corn, [8.5, 9.5, 10.5, 11.5]).items(): print(f"  {k} córners: {pct(v)}  (Under {pct(1-v)})")
    print(f"  Más córners: {META['home']} {pct(np.mean(cornH>cornA))} | Empate {pct(np.mean(cornH==cornA))} | {META['away']} {pct(np.mean(cornA>cornH))}")

    print(f"\n🟨 TARJETAS  (esp {yellows.mean():.1f} amarillas; árbitro {ref.get('name','?')})")
    for k, v in ou_lines(yellows, [3.5, 4.5, 5.5, 6.5]).items(): print(f"  {k} amarillas: {pct(v)}  (Under {pct(1-v)})")
    print(f"  Al menos 1 ROJA en el partido: {pct(np.mean(reds>=1))}")
    print(f"  Puntos de reserva (booking) Over 30.5: {pct(np.mean(booking_pts>30.5))} | Over 40.5: {pct(np.mean(booking_pts>40.5))}")

    print(f"\n🤾 FALTAS  (esp {fouls.mean():.1f} total)")
    for k, v in ou_lines(fouls, [20.5, 22.5, 24.5, 26.5]).items(): print(f"  {k} faltas: {pct(v)}  (Under {pct(1-v)})")

    print(f"\n🎯 TIROS  (esp {shotsH.mean():.1f}-{shotsA.mean():.1f})")
    print(f"  Over 24.5 tiros totales: {pct(np.mean(shotsH+shotsA>24.5))}")

    print(f"\n⚽ GOLEADORES — ANYTIME (anota en cualquier momento)")
    allsc = sorted([(META['home'], p['name'], anyH[i], egH_pl[i]) for i, p in enumerate(M['home']['players'])] +
                   [(META['away'], p['name'], anyA[i], egA_pl[i]) for i, p in enumerate(M['away']['players'])], key=lambda x: -x[2])
    for tm, nm, a, eg in allsc[:10]: print(f"  {nm:<22} ({tm[:3]})  {pct(a)}  (goles esp {eg:.2f})")
    print(f"\n⚽ PRIMER GOLEADOR (top 6)   |   Sin goles (0-0): {pct(p_nogoal)}")
    allf = sorted([(META['home'], p['name'], firstH[i]) for i, p in enumerate(M['home']['players'])] +
                  [(META['away'], p['name'], firstA[i]) for i, p in enumerate(M['away']['players'])], key=lambda x: -x[2])
    for tm, nm, f in allf[:6]: print(f"  {nm:<22} ({tm[:3]})  {pct(f)}")

    print(f"\n🟨 QUIÉN VE AMARILLA (probabilidad por jugador, top 10)")
    booked = sorted(zip(teams_all, names_all, p_booked), key=lambda x: -x[2])
    for tm, nm, pb in booked[:10]: print(f"  {nm:<22} ({tm[:3]})  {pct(pb)}")

    R = dict(meta=META, referee=ref, stats={'home': stH, 'away': stA},
             goals=dict(pH=float(hw), pD=float(dr), pA=float(aw), egH=float(gm.mean()), egA=float(ga.mean()),
                        over25=float(np.mean(tot>=3)), btts=float(np.mean((gm>=1)&(ga>=1))), top=[[int(a),int(b),c/n] for (a,b),c in top]),
             corners=dict(total=float(corn.mean()), over95=float(np.mean(corn>9.5))),
             cards=dict(yellows=float(yellows.mean()), over45=float(np.mean(yellows>4.5)), red=float(np.mean(reds>=1))),
             fouls=dict(total=float(fouls.mean())),
             scorers_anytime=[[tm, nm, float(a)] for tm, nm, a, eg in allsc[:12]],
             first_scorer=[[tm, nm, float(f)] for tm, nm, f in allf[:8]],
             bookings=[[tm, nm, float(pb)] for tm, nm, pb in booked[:12]])
    json.dump(R, open(os.path.join(ROOT, "final_ARG_ESP.json"), "w", encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f"\n{'='*64}\n✅ Listo en {time.time()-t0:.0f}s | GLM {USAGE['calls']} calls, {USAGE['out']:,} out tokens")
    print("   Guardado: final_ARG_ESP.json")

if __name__ == "__main__":
    main()
