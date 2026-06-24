#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corre los partidos de hoy desde 0 con GLM (modelo completo) y compara vs las predicciones de Claude."""
import json, time
from glm_research import research_match, USAGE
from export_predictions import metrics

MATCHES = [
    {"id": "CZE_MEX", "home": "Czechia", "away": "Mexico", "group": "A", "venue": "Estadio Azteca, CDMX (2240m altitud)", "host": "Mexico"},
    {"id": "RSA_KOR", "home": "South Africa", "away": "South Korea", "group": "A", "venue": "Estadio BBVA, Monterrey", "host": ""},
    {"id": "SUI_CAN", "home": "Switzerland", "away": "Canada", "group": "B", "venue": "BC Place, Vancouver", "host": "Canada"},
    {"id": "SCO_BRA", "home": "Scotland", "away": "Brazil", "group": "C", "venue": "Hard Rock Stadium, Miami", "host": ""},
]

def p1x2(M):
    d = {x["selection"]: x["prob"] for x in metrics(M)["markets"] if x["market"] == "1X2"}
    return d

def main():
    rows = []
    for mt in MATCHES:
        claude = json.load(open(f"match_{mt['id']}.json", encoding="utf-8"))
        cp = p1x2(claude)
        g = dict(mt); g["id"] = mt["id"] + "_GLM"
        print(f"🧠 GLM: {mt['home']} vs {mt['away']}...")
        research_match(g)
        glm = json.load(open(f"match_{g['id']}.json", encoding="utf-8"))
        gp = p1x2(glm)
        rows.append((mt, cp, gp))

    print("\n" + "=" * 78)
    print("  COMPARACION: CLAUDE vs GLM (modelo completo) — partidos de hoy")
    print("=" * 78)
    print(f"  {'PARTIDO':30}{'FUENTE':8}{'Local':>8}{'Empate':>8}{'Visit':>8}")
    for mt, cp, gp in rows:
        h, a = mt["home"], mt["away"]
        name = f"{h[:13]} v {a[:13]}"
        print(f"  {name:30}{'Claude':8}{cp.get(h,0)*100:7.1f}%{cp.get('Empate',0)*100:7.1f}%{cp.get(a,0)*100:7.1f}%")
        print(f"  {'':30}{'GLM':8}{gp.get(h,0)*100:7.1f}%{gp.get('Empate',0)*100:7.1f}%{gp.get(a,0)*100:7.1f}%")
        dh = abs(cp.get(h,0)-gp.get(h,0))*100
        print(f"  {'':30}{'Δ local':8}{dh:7.1f}%")
    print(f"\n  GLM total: {USAGE['calls']} llamadas | {USAGE['in']:,} in | {USAGE['out']:,} out")
    print("=" * 78)

if __name__ == "__main__":
    main()
