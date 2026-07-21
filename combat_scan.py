#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOTOR DE COMBATE (MMA/UFC + Box) — Wuru v1.
  1. Trae peleas con momios (The Odds API: mma_mixed_martial_arts, boxing_boxing).
  2. GLM investiga a CADA peleador (gemelo: estilo, alcance, edad, campamento, corte de peso,
     mentón/cardio, racha, psicología) + análisis del cruce de estilos. Consenso x2.
  3. Prob efectiva = 30% modelo + 70% mercado (de-vig) -> edge -> reporte de valor.
Uso: python3 combat_scan.py [VENTANA_H=168]
"""
import json, sys, os, re, urllib.request, datetime as dt
from concurrent.futures import ThreadPoolExecutor
from statistics import median
from glm_research import glm, parse_json, USAGE

ROOT = os.path.dirname(os.path.abspath(__file__))
def env_val(k, d=""):
    v = os.environ.get(k)
    if v: return v
    try:
        for line in open(os.path.join(ROOT, "wuru-bets/.env"), encoding="utf-8"):
            if line.startswith(k + "="): return line.strip().split("=", 1)[1]
    except Exception: pass
    return d
KEY = env_val("ODDS_API_KEY"); REGIONS = env_val("ODDS_REGIONS", "us,uk,eu")
SPORTS = [("mma_mixed_martial_arts", "MMA"), ("boxing_boxing", "Box")]

def fetch_fights(window_h):
    now = dt.datetime.now(dt.timezone.utc); out = []
    for sk, lbl in SPORTS:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{sk}/odds?regions={REGIONS}&markets=h2h&oddsFormat=decimal&apiKey={KEY}"
            for ev in json.load(urllib.request.urlopen(url, timeout=30)):
                ct = ev.get("commence_time")
                if not ct: continue
                h = (dt.datetime.fromisoformat(ct.replace("Z", "+00:00")) - now).total_seconds() / 3600
                if not (0 <= h <= window_h): continue
                arr = {}
                for bk in ev.get("bookmakers", []):
                    for mk in bk.get("markets", []):
                        if mk["key"] == "h2h":
                            for o in mk["outcomes"]:
                                if 1.01 < o["price"] < 30: arr.setdefault(o["name"], []).append(o["price"])
                a, b = ev["home_team"], ev["away_team"]
                if a in arr and b in arr and len(arr[a]) >= 2:
                    out.append({"sport": lbl, "a": a, "b": b, "oa": median(arr[a]), "ob": median(arr[b]), "when": ct, "hrs": h})
        except Exception as e:
            print(f"  ⚠️ {sk}: {e}")
    return out

def devig2(oa, ob):
    ra, rb = 1 / oa, 1 / ob; s = ra + rb
    return ra / s, rb / s

def fighter_twin(name, opp, sport):
    p = (f"Eres analista de {('MMA/UFC' if sport=='MMA' else 'boxeo')} de élite. Investiga con WEB SEARCH a {name}, "
         f"que pelea próximamente vs {opp}.\n"
         f"Profundiza: récord y racha reciente (últimas 5 peleas, cómo ganó/perdió), estilo (striker/grappler/presión/contragolpe), "
         f"alcance/estatura/edad (¿en declive?), campamento actual (¿cambió de gym/coach?), historial de corte de peso, "
         f"mentón/durabilidad (KOs recibidos), cardio en rounds tardíos, lesiones, vida personal/motivación, actividad reciente (ring rust).\n"
         'Responde SOLO JSON: {"name":"...","record":"W-L","age":int,"reach_cm":num,"style":"...","striking":0-100,'
         '"grappling":0-100,"chin":0-100,"cardio":0-100,"power":0-100,"iq":0-100,"weight_cut_risk":0-100,'
         '"ring_rust":0-100,"motivation":0-100,"decline":0-100,"notes":"3 lineas clave","sources":"..."}. Sin texto extra.')
    return parse_json(glm(p, max_tokens=2200))

def matchup_prob(fa, fb, a, b, sport):
    p = (f"Analiza el cruce {a} vs {b} ({sport}). Datos investigados:\n{json.dumps(fa,ensure_ascii=False)}\n{json.dumps(fb,ensure_ascii=False)}\n"
         f"Considera choque de estilos, alcance, edad/declive, cardio, corte de peso, motivación.\n"
         f'Responde SOLO JSON: {{"p_{"a"}":0-1}} = probabilidad REALISTA de que gane {a}. Sin texto extra.')
    try:
        r = parse_json(glm(p, web=False, max_tokens=400))
        v = float(list(r.values())[0])
        return min(max(v, 0.03), 0.97)
    except Exception:
        return None

def main():
    window = int(sys.argv[1]) if len(sys.argv) > 1 else 168
    print(f"🥊 MOTOR DE COMBATE — peleas próximas ({window}h)...")
    fights = fetch_fights(window)
    print(f"   {len(fights)} peleas con momios\n")
    if not fights: return
    W_MODEL = 0.30
    results = []
    for f in fights:
        print(f"🔎 {f['sport']}: {f['a']} vs {f['b']} ({f['hrs']:.0f}h)")
        try:
            with ThreadPoolExecutor(2) as ex:
                ta = ex.submit(fighter_twin, f["a"], f["b"], f["sport"])
                tb = ex.submit(fighter_twin, f["b"], f["a"], f["sport"])
                fa, fb = ta.result(), tb.result()
            ps = [x for x in (matchup_prob(fa, fb, f["a"], f["b"], f["sport"]) for _ in range(2)) if x]
            if not ps: print("   ⚠️ sin prob del modelo"); continue
            pm = sum(ps) / len(ps)
            mka, mkb = devig2(f["oa"], f["ob"])
            effa = W_MODEL * pm + (1 - W_MODEL) * mka
            effb = W_MODEL * (1 - pm) + (1 - W_MODEL) * mkb
            ea, eb = effa * f["oa"] - 1, effb * f["ob"] - 1
            best = (f["a"], f["oa"], effa, ea) if ea >= eb else (f["b"], f["ob"], effb, eb)
            tag = "💎 VALOR" if best[3] >= 0.05 and best[2] >= 0.25 else "—"
            print(f"   modelo: {f['a']} {pm*100:.0f}% | mercado {mka*100:.0f}% | mejor: {best[0]} @ {best[1]:.2f} edge {best[3]*100:+.1f}% {tag}")
            results.append({**f, "p_model": pm, "p_mkt_a": mka, "twin_a": fa, "twin_b": fb,
                            "best": best[0], "best_odds": best[1], "edge": best[3], "value": tag != "—"})
        except Exception as e:
            print(f"   ⚠️ {e}")
    json.dump(results, open(os.path.join(ROOT, "combat_value.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    vals = [r for r in results if r["value"]]
    print(f"\n{'='*64}\n🏆 VALOR ENCONTRADO: {len(vals)} de {len(results)} peleas analizadas")
    for r in vals: print(f"   {r['sport']}: {r['best']} @ {r['best_odds']:.2f} (edge {r['edge']*100:+.1f}%) vs {r['a'] if r['best']!=r['a'] else r['b']}")
    print(f"   GLM: {USAGE['calls']} calls | guardado combat_value.json")

if __name__ == "__main__": main()
