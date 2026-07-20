#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LIGA MX APERTURA 2026 — JORNADA 2 (quiniela): modelo COMPLETO en los 9 partidos.
  fase research: GLM investiga 11v11 (22 gemelos) + entorno por partido (sin simplificar).
  fase sim:      1,000,000 Monte Carlo por partido con Elo Liga MX (investigado por Opus)
                 -> 1X2, goles esperados, marcadores, quiniela final.
Uso: python3 jornada2.py research | sim
"""
import json, os, sys, time
import numpy as np
from collections import Counter
from multiprocessing import Pool, cpu_count
from glm_research import research_match, USAGE
import sim_match as SM

ROOT = os.path.dirname(os.path.abspath(__file__))
COMP = "Liga MX Apertura 2026, Jornada 2 (julio 2026)"
MATCHES = [
    ("CAZ_PUE", "Cruz Azul", "Puebla"),
    ("TOL_PUM", "Toluca", "Pumas"),
    ("TIJ_LEO", "Tijuana", "León"),
    ("ATE_AME", "Atlante", "América"),
    ("CHI_JUA", "Chivas", "Juárez"),
    ("SAN_ATL", "Santos", "Atlas"),
    ("TIG_SLU", "Tigres", "San Luis"),
    ("NEC_MTY", "Necaxa", "Monterrey"),
    ("PAC_QUE", "Pachuca", "Querétaro"),
]
def meta_of(mid, h, a):
    return {"id": mid, "home": h, "away": a, "group": "Jornada 2",
            "venue": f"Estadio de {h} (local), México", "host": h, "comp": COMP}

def do_research():
    print(f"🧠 GLM: investigación COMPLETA de {len(MATCHES)} partidos (22 gemelos c/u)...")
    t0 = time.time()
    for mid, h, a in MATCHES:
        mf = os.path.join(ROOT, f"match_{mid}.json")
        if os.path.exists(mf) and os.path.getsize(mf) > 40_000:
            print(f"  ↺ {mid} ya investigado (reuso)"); continue
        try:
            research_match(meta_of(mid, h, a))
        except Exception as e:
            print(f"  ⚠️ {mid}: {e}")
    print(f"✅ Research listo en {(time.time()-t0)/60:.1f} min | GLM {USAGE['calls']} calls, {USAGE['in']:,} in / {USAGE['out']:,} out")

def sim_goals(M, n_total):
    AH = SM.arr(M['home']['players']); AA = SM.arr(M['away']['players'])
    bh = SM.base_idx(AH); ba = SM.base_idx(AA); env = M.get('env') or {}
    meta = M['meta']; hh = meta.get('host') == meta.get('home'); ha = meta.get('host') == meta.get('away')
    lamH, lamA = SM.elo_base_lams(meta['home'], meta['away'], hh, ha)
    cores = max(cpu_count() - 1, 1); chunk = n_total // cores
    with Pool(cores) as pool:
        res = pool.map(SM.worker, [(AH, AA, env, hh, ha, chunk, 7 + i, bh, ba, lamH, lamA) for i in range(cores)])
    gm = np.concatenate([r[0] for r in res]).astype(int); ga = np.concatenate([r[1] for r in res]).astype(int)
    return gm, ga

def do_sim(n_total=1_000_000):
    # Elo Liga MX investigado (Opus) -> se inyecta al motor
    elo_f = os.path.join(ROOT, "ligamx_elo.json")
    if not os.path.exists(elo_f):
        print("❌ Falta ligamx_elo.json (fuerza de clubes). Córrelo cuando esté."); sys.exit(1)
    lelo = json.load(open(elo_f, encoding='utf-8'))
    for k, v in lelo.get('elo', lelo).items():
        if isinstance(v, (int, float)): SM.ELO[k.lower()] = float(v)
    print(f"📈 Elo Liga MX cargado ({len([v for v in lelo.get('elo', lelo).values() if isinstance(v,(int,float))])} clubes)")

    out = []
    print(f"🎲 Simulando {n_total:,} partidos × {len(MATCHES)}...")
    for mid, h, a in MATCHES:
        mf = os.path.join(ROOT, f"match_{mid}.json")
        if not os.path.exists(mf):
            print(f"  ⚠️ {mid}: sin research, salto"); continue
        M = json.load(open(mf, encoding='utf-8'))
        gm, ga = sim_goals(M, n_total)
        n = len(gm); tot = gm + ga
        pH, pD, pA = float(np.mean(gm > ga)), float(np.mean(gm == ga)), float(np.mean(gm < ga))
        top = Counter(zip(gm.tolist(), ga.tolist())).most_common(3)
        pick = "LOCAL" if pH >= max(pD, pA) else ("EMPATE" if pD >= pA else "VISITANTE")
        r = dict(id=mid, home=h, away=a, pH=pH, pD=pD, pA=pA, pick=pick,
                 egH=float(gm.mean()), egA=float(ga.mean()), eg_total=float(tot.mean()),
                 over25=float(np.mean(tot >= 3)), btts=float(np.mean((gm >= 1) & (ga >= 1))),
                 scores=[[int(x), int(y), c / n] for (x, y), c in top])
        out.append(r)
        print(f"  {h} vs {a}: {pick} | {pH*100:.0f}/{pD*100:.0f}/{pA*100:.0f} | goles {r['eg_total']:.2f}")
    json.dump(out, open(os.path.join(ROOT, "jornada2_results.json"), "w", encoding='utf-8'), ensure_ascii=False, indent=2)

    print(f"\n{'='*74}\n📋 QUINIELA JORNADA 2 — modelo completo, {n_total:,} sims/partido\n{'='*74}")
    print(f"{'PARTIDO':<26}{'PICK':<11}{'L%':>5}{'E%':>5}{'V%':>5}   {'GOLES':>5}  MARCADOR")
    for r in out:
        sc = f"{r['scores'][0][0]}-{r['scores'][0][1]} ({r['scores'][0][2]*100:.0f}%)"
        print(f"{r['home']+' vs '+r['away']:<26}{r['pick']:<11}{r['pH']*100:>4.0f} {r['pD']*100:>4.0f} {r['pA']*100:>4.0f}   {r['eg_total']:>5.2f}  {sc}")

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "research"
    if mode == "research": do_research()
    elif mode == "sim": do_sim()
