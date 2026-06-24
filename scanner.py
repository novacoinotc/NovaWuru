#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESCANER MULTI-LIGA Wuru:
  1. Trae TODOS los partidos de fútbol con momios (todas las ligas activas, ventana).
  2. 1 llamada GLM rápida por partido -> prob 1X2 -> edge vs mercado.
  3. Rankea por valor -> TOP N (15).
  4. A esos 15 les corre el MODELO COMPLETO (research_match) + seed -> Neon.
Uso: python3 scanner.py [TOP_N=15] [WINDOW_H=36]
"""
import json, sys, os, re, time, urllib.request, subprocess, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
from glm_research import glm, parse_json, research_match, USAGE

ROOT = os.path.dirname(os.path.abspath(__file__))
def env_val(k, d=""):
    v = os.environ.get(k)
    if v: return v
    try:
        for line in open(os.path.join(ROOT, "wuru-bets/.env"), encoding="utf-8"):
            if line.startswith(k + "="): return line.strip().split("=", 1)[1]
    except Exception: pass
    return d
ODDS_KEY = env_val("ODDS_API_KEY"); REGIONS = env_val("ODDS_REGIONS", "us,uk,eu")
HOSTS = {"mexico", "united states", "usa", "canada"}

def get_leagues():
    d = json.load(urllib.request.urlopen(f"https://api.the-odds-api.com/v4/sports/?apiKey={ODDS_KEY}", timeout=30))
    return [s["key"] for s in d if s["key"].startswith("soccer") and s.get("active") and "winner" not in s["key"]]

def fetch_matches(window_h):
    now = dt.datetime.now(dt.timezone.utc); out = []
    for lg in get_leagues():
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{lg}/odds?regions={REGIONS}&markets=h2h&oddsFormat=decimal&apiKey={ODDS_KEY}"
            for ev in json.load(urllib.request.urlopen(url, timeout=25)):
                ct = ev.get("commence_time");
                if not ct: continue
                h = (dt.datetime.fromisoformat(ct.replace("Z","+00:00")) - now).total_seconds()/3600
                if not (0 <= h <= window_h): continue
                # mediana de momios h2h
                from collections import defaultdict
                arr = defaultdict(list)
                for bk in ev.get("bookmakers", []):
                    for mk in bk.get("markets", []):
                        if mk["key"] == "h2h":
                            for o in mk["outcomes"]:
                                if 1.01 < o["price"] < 100: arr[o["name"]].append(o["price"])
                def med(a): a=sorted(a); return a[len(a)//2] if a else 0
                home, away = ev["home_team"], ev["away_team"]
                oh, od, oa = med(arr.get(home,[])), med(arr.get("Draw",[])), med(arr.get(away,[]))
                if oh and oa:
                    out.append({"league": lg, "home": home, "away": away, "oh": oh, "od": od, "oa": oa, "when": ct})
        except Exception: pass
    return out

def devig3(oh, od, oa):
    raw = [1/oh, 1/od if od else 0, 1/oa]
    lo, hi = 0.5, 1.5
    for _ in range(60):
        mid = (lo+hi)/2; s = sum(p**mid for p in raw if p>0)
        if s > 1: lo = mid
        else: hi = mid
    k = (lo+hi)/2; return [p**k for p in raw]

def quick_probs(m):
    p = (f"Probabilidad realista del resultado (1X2) de {m['home']} vs {m['away']} (futbol de club, liga {m['league']}). "
         'Responde SOLO JSON: {"home":0-1,"draw":0-1,"away":0-1} (suman ~1).')
    try:
        q = parse_json(glm(p, web=False, max_tokens=200))
        return [float(q.get("home",0)), float(q.get("draw",0)), float(q.get("away",0))]
    except Exception:
        return None

def edge_of(m):
    qp = quick_probs(m)
    if not qp: return -1
    mk = devig3(m["oh"], m["od"], m["oa"])
    odds = [m["oh"], m["od"], m["oa"]]
    # mezcla 30/70 y edge max
    best = -1
    for i in range(3):
        eff = 0.3*qp[i] + 0.7*mk[i]
        if odds[i] and odds[i] <= 7:
            best = max(best, eff*odds[i]-1)
    return best

def mk_id(h, a, taken):
    c = lambda s: re.sub(r"[^A-Z]","",s.upper())[:3] or "XXX"
    base = f"{c(h)}_{c(a)}"; i, n = base, 1
    while i in taken: n+=1; i=f"{base}{n}"
    taken.add(i); return i

def main():
    top_n = int(sys.argv[1]) if len(sys.argv)>1 else 15
    window = int(sys.argv[2]) if len(sys.argv)>2 else 120  # 5 dias: capturar momios tempranos
    print(f"🔎 Escaneando todas las ligas (ventana {window}h)...")
    ms = fetch_matches(window)
    print(f"   {len(ms)} partidos con momios encontrados")
    if not ms: return
    print("⚡ Scan rápido (GLM 1 call/partido) para rankear por valor...")
    with ThreadPoolExecutor(8) as ex:
        futs = {ex.submit(edge_of, m): m for m in ms}
        for f in as_completed(futs): futs[f]["edge"] = f.result()
    ranked = sorted(ms, key=lambda m: m.get("edge",-1), reverse=True)
    top = [m for m in ranked if m.get("edge",-1) >= 0.03][:top_n]
    print(f"\n🏆 TOP {len(top)} por valor estimado:")
    for m in top: print(f"   {m['edge']*100:5.1f}%  {m['home']} vs {m['away']}  ({m['league']})")
    if not top: print("Sin candidatos de valor."); return

    print(f"\n🧠 Modelo COMPLETO a los {len(top)}...")
    taken = set()
    for m in top:
        meta = {"id": mk_id(m["home"], m["away"], taken), "home": m["home"], "away": m["away"],
                "group": "", "venue": m["league"].replace("soccer_","").replace("_"," ").title(),
                "host": m["home"] if m["home"].lower() in HOSTS else (m["away"] if m["away"].lower() in HOSTS else "")}
        mf = os.path.join(ROOT, f"match_{meta['id']}.json")
        if os.path.exists(mf) and os.path.getsize(mf) > 64_000:  # reusa SOLO si ya es profundo (GLM-deep ~69KB+)
            print(f"  ↺ {meta['id']} ya investigado a profundidad (reuso)"); continue
        try: research_match(meta)
        except Exception as e: print(f"  ⚠️ {meta['id']}: {e}")
    print(f"   GLM total: {USAGE['calls']} calls | {USAGE['in']:,} in | {USAGE['out']:,} out")

    print("\n📊 export + 💸 seed (Neon, momios reales multi-liga)...")
    subprocess.run([sys.executable, "export_predictions.py"], cwd=ROOT, check=True, capture_output=True)
    r = subprocess.run("npm run accrue", cwd=os.path.join(ROOT,"wuru-bets"), shell=True, capture_output=True, text=True)
    print("   " + (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]))
    print("\n✅ Listo. Dashboard: https://nova-wuru.vercel.app")

if __name__ == "__main__": main()
