#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AUTO-LIQUIDACION: jala resultados reales (The Odds API /scores) de todas las ligas,
escribe results.json (keyed por nombres normalizados) y corre `npm run settle` (Neon).
Uso: python3 settle_auto.py [DIAS_ATRAS=3]
"""
import json, sys, os, re, unicodedata, urllib.request, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
def env_val(k, d=""):
    v = os.environ.get(k)
    if v: return v
    try:
        for line in open(os.path.join(ROOT, "wuru-bets/.env"), encoding="utf-8"):
            if line.startswith(k + "="): return line.strip().split("=", 1)[1]
    except Exception: pass
    return d
ODDS_KEY = env_val("ODDS_API_KEY")
LEAGUES = (env_val("ODDS_SPORT_KEYS") or env_val("ODDS_SPORT_KEY", "soccer_fifa_world_cup")).split(",")

def norm(s):  # debe coincidir con settle.ts
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", s)

def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    results = {}
    for lg in LEAGUES:
        lg = lg.strip()
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{lg}/scores/?daysFrom={days}&apiKey={ODDS_KEY}"
            for ev in json.load(urllib.request.urlopen(url, timeout=25)):
                if not ev.get("completed"): continue
                sc = {s["name"]: int(s["score"]) for s in (ev.get("scores") or []) if s.get("score") is not None}
                hg = sc.get(ev["home_team"]); ag = sc.get(ev["away_team"])
                if hg is None or ag is None: continue
                results[f"{norm(ev['home_team'])}|{norm(ev['away_team'])}"] = {"hg": hg, "ag": ag}
        except Exception: pass
    json.dump(results, open(os.path.join(ROOT, "results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"📥 {len(results)} resultados finales obtenidos")
    r = subprocess.run("npm run settle", cwd=os.path.join(ROOT, "wuru-bets"), shell=True, capture_output=True, text=True)
    print("   " + (r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]))

if __name__ == "__main__":
    main()
