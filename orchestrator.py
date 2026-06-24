#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ORQUESTADOR DIARIO Wuru — automatiza todo:
  1. Descubre partidos proximos (The Odds API, ventana configurable).
  2. Investiga cada uno con GLM (paralelo) -> match_<ID>.json.
  3. Simula (sim_match) -> export_predictions.py -> predictions.json.
  4. Coloca apuestas de valor con momios reales (npm run seed en wuru-bets).
Uso: python3 orchestrator.py [HORAS_VENTANA=36] [MAX_PARTIDOS=8]
"""
import json, sys, os, re, time, urllib.request, subprocess, datetime as dt

ROOT = os.path.dirname(os.path.abspath(__file__))
def env_val(k, default=""):
    v = os.environ.get(k)
    if v: return v
    try:
        for line in open(os.path.join(ROOT, "wuru-bets/.env"), encoding="utf-8"):
            if line.startswith(k + "="): return line.strip().split("=", 1)[1]
    except Exception: pass
    return default

ODDS_KEY = env_val("ODDS_API_KEY")
SPORT = env_val("ODDS_SPORT_KEY", "soccer_fifa_world_cup")
HOSTS = {"mexico": "Mexico", "united states": "USA", "usa": "USA", "canada": "Canada"}

def fetch_upcoming(hours):
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds?regions=us,uk,eu&markets=h2h&oddsFormat=decimal&apiKey={ODDS_KEY}"
    data = json.load(urllib.request.urlopen(url, timeout=60))
    now = dt.datetime.now(dt.timezone.utc)
    out = []
    for ev in data:
        ct = ev.get("commence_time")
        if not ct: continue
        when = dt.datetime.fromisoformat(ct.replace("Z", "+00:00"))
        h = (when - now).total_seconds() / 3600
        if 0 <= h <= hours:
            out.append((when, ev["home_team"], ev["away_team"]))
    out.sort()
    return out

def mk_id(home, away, taken):
    def code(s): return re.sub(r"[^A-Z]", "", s.upper())[:3] or "XXX"
    base = f"{code(home)}_{code(away)}"; i = base; n = 1
    while i in taken: n += 1; i = f"{base}{n}"
    taken.add(i); return i

def host_of(home, away):
    if home.lower() in HOSTS: return home
    if away.lower() in HOSTS: return away
    return ""

def main():
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 36
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    if not ODDS_KEY:
        print("Falta ODDS_API_KEY"); return
    print(f"🔎 Buscando partidos en las proximas {hours}h...")
    ups = fetch_upcoming(hours)[:cap]
    if not ups:
        print("No hay partidos proximos en la ventana."); return
    print(f"   {len(ups)} partidos:")
    for when, h, a in ups: print(f"     {when:%d-%b %H:%M}Z  {h} vs {a}")

    from glm_research import research_match, USAGE
    import importlib
    taken = set(); metas = []
    for when, h, a in ups:
        metas.append({"id": mk_id(h, a, taken), "home": h, "away": a, "group": "", "venue": "Sede Mundial 2026", "host": host_of(h, a)})

    print("\n🧠 Investigando con GLM (paralelo)...")
    t0 = time.time()
    for m in metas:
        try: research_match(m)
        except Exception as e: print(f"  ⚠️ {m['id']} fallo: {e}")
    print(f"   GLM total: {USAGE['calls']} llamadas | {USAGE['in']:,} in | {USAGE['out']:,} out | {time.time()-t0:.0f}s")

    print("\n📊 Generando predicciones...")
    subprocess.run([sys.executable, "export_predictions.py"], cwd=ROOT, check=True)

    print("\n💸 Colocando apuestas de valor (momios reales)...")
    r = subprocess.run("npm run seed", cwd=os.path.join(ROOT, "wuru-bets"), shell=True, capture_output=True, text=True)
    print("   " + (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]))
    print("\n✅ Orquestacion completa. Dashboard: http://localhost:3000")

if __name__ == "__main__":
    main()
