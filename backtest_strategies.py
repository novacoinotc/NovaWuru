#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKTEST DE ESTRATEGIAS DE APUESTAS sobre partidos del Mundial ya jugados.
Datos: backtest.json (prob REAL del modelo GLM + resultado REAL) + elo.json (proxy de mercado).
Prueba: 3 estrategias de valor + 2 baselines ("apostar al ganador", "apostar al favorito").
Mide: P&L, ROI, # apuestas, % acierto, drawdown. + bootstrap de significancia.

Honesto: 28 partidos (muestra chica) y momios = proxy Elo (no momios reales de cierre).
=> sirve para COMPARAR estrategias entre sí (ranking), no para ROI absoluto exacto.
"""
import json, math, random
from collections import defaultdict

random.seed(42)
BT = json.load(open("backtest.json"))
ELO = json.load(open("elo.json"))
fixtures = {(f["home"], f["away"]): f for f in BT["fixtures"]}
preds = BT["predictions"]

# ---------- Mercado proxy: Elo -> lambdas -> Poisson 1X2 ----------
def poisson_1x2(lh, la, maxg=10):
    ph = pd = pa = 0.0
    for i in range(maxg + 1):
        for j in range(maxg + 1):
            p = (math.exp(-lh) * lh**i / math.factorial(i)) * (math.exp(-la) * la**j / math.factorial(j))
            if i > j: ph += p
            elif i == j: pd += p
            else: pa += p
    return ph, pd, pa

def market_probs(home, away, host):
    eh, ea = ELO.get(home, 1600), ELO.get(away, 1600)
    hfa = 70 if host and host.lower() == home.lower() else 0
    dr = (eh + hfa) - ea
    sup = dr / 130.0          # ~400 Elo ≈ 3 goles de diferencia
    total = 2.6
    lh = max(0.15, (total + sup) / 2); la = max(0.15, (total - sup) / 2)
    return poisson_1x2(lh, la)

def vig_odds(probs, overround=1.06):
    s = sum(probs)
    book = [p / s * overround for p in probs]
    return [1.0 / b for b in book]   # momios que ofrecería la casa (con jugo)

# ---------- Motor de apuestas (igual que producción) ----------
W_MODEL, EDGE_CAP, MAX_ODDS, EV_TH = 0.30, 0.15, 7.0, 0.05
FRAC, MAXPCT = 0.25, 0.03

def kelly_stake(bankroll, p, odds):
    b = odds - 1
    if b <= 0: return 0
    k = (b * p - (1 - p)) / b
    if k <= 0: return 0
    return min(bankroll * k * FRAC, bankroll * MAXPCT)

def outcome_win(sel, f):  # sel in {H,D,A}
    hg, ag = f["hg"], f["ag"]
    return (sel == "H" and hg > ag) or (sel == "A" and ag > hg) or (sel == "D" and hg == ag)

# Construye, por partido, las 3 selecciones con: prob modelo, prob mercado (de-vig), momio
MATCHES = []
for p in preds:
    f = fixtures.get((p["home"], p["away"]))
    if not f: continue
    model = [p["p_home"], p["p_draw"], p["p_away"]]
    mk_raw = market_probs(p["home"], p["away"], f.get("host", ""))
    odds = vig_odds(mk_raw)
    s = sum(mk_raw); mk_devig = [x / s for x in mk_raw]   # prob mercado sin jugo
    MATCHES.append({"home": p["home"], "away": p["away"], "f": f,
                    "model": model, "mk": mk_devig, "odds": odds})

LBL = ["H", "D", "A"]

def run_strategy(prob_floor, label):
    """Estrategia de valor con piso de probabilidad efectiva."""
    bank = 100000.0; peak = bank; maxdd = 0.0
    nbets = wins = 0; staked = 0.0
    for m in MATCHES:
        for i in range(3):
            model, mk, odds = m["model"][i], m["mk"][i], m["odds"][i]
            eff = W_MODEL * model + (1 - W_MODEL) * mk
            edge = eff * odds - 1
            if edge < EV_TH or edge > EDGE_CAP or odds < 1.2 or odds > MAX_ODDS: continue
            if eff < prob_floor: continue
            stake = kelly_stake(bank, eff, odds)
            if stake < 50: continue
            won = outcome_win(LBL[i], m["f"])
            bank += stake * (odds - 1) if won else -stake
            nbets += 1; wins += won; staked += stake
            peak = max(peak, bank); maxdd = max(maxdd, (peak - bank) / peak)
    return {"label": label, "bank": bank, "roi": (bank - 100000) / 100000,
            "nbets": nbets, "hit": wins / nbets if nbets else 0,
            "yield": (bank - 100000) / staked if staked else 0, "maxdd": maxdd}

def run_baseline(pick, label, flat=0.02):
    """pick: 'model_winner' (favorito del modelo) o 'market_fav' (momio mas bajo). Stake plano."""
    bank = 100000.0; peak = bank; maxdd = 0.0; nbets = wins = 0; staked = 0.0
    for m in MATCHES:
        i = (max(range(3), key=lambda k: m["model"][k]) if pick == "model_winner"
             else min(range(3), key=lambda k: m["odds"][k]))
        stake = bank * flat
        won = outcome_win(LBL[i], m["f"])
        bank += stake * (m["odds"][i] - 1) if won else -stake
        nbets += 1; wins += won; staked += stake
        peak = max(peak, bank); maxdd = max(maxdd, (peak - bank) / peak)
    return {"label": label, "bank": bank, "roi": (bank - 100000) / 100000,
            "nbets": nbets, "hit": wins / nbets if nbets else 0,
            "yield": (bank - 100000) / staked if staked else 0, "maxdd": maxdd}

STRATS = [("Piso 0.00 (puro)", 0.0), ("Piso 0.20", 0.20), ("Piso 0.25", 0.25),
          ("Piso 0.30", 0.30), ("Piso 0.33 (equil)", 0.33), ("Piso 0.40", 0.40), ("Piso 0.45 (cons)", 0.45)]
results = [run_strategy(f, l) for l, f in STRATS]
results.append(run_baseline("model_winner", "BASELINE: apostar al ganador (modelo)"))
results.append(run_baseline("market_fav", "BASELINE: apostar al favorito (momio)"))

print(f"\n{'='*78}\nBACKTEST ESTRATEGIAS · {len(MATCHES)} partidos Mundial 2026 (ya jugados)\n{'='*78}")
print(f"{'Estrategia':<42}{'ROI':>8}{'Bank':>11}{'#Ap':>5}{'Acierto':>9}{'MaxDD':>8}")
print("-" * 78)
for r in results:
    print(f"{r['label']:<42}{r['roi']*100:>6.1f}% {r['bank']:>10,.0f}{r['nbets']:>5}{r['hit']*100:>7.0f}% {r['maxdd']*100:>6.1f}%")

# ---------- Bootstrap: ¿el ranking es robusto o suerte? (resamplea partidos) ----------
print(f"\n{'='*78}\nBOOTSTRAP (2000 resamples de los {len(MATCHES)} partidos) · ROI medio ± rango\n{'='*78}")
def boot_strategy(prob_floor, B=2000):
    rois = []
    for _ in range(B):
        sample = [random.choice(MATCHES) for _ in MATCHES]
        bank = 100000.0
        for m in sample:
            for i in range(3):
                eff = W_MODEL * m["model"][i] + (1 - W_MODEL) * m["mk"][i]
                edge = eff * m["odds"][i] - 1
                if edge < EV_TH or edge > EDGE_CAP or m["odds"][i] < 1.2 or m["odds"][i] > MAX_ODDS: continue
                if eff < prob_floor: continue
                stake = kelly_stake(bank, eff, m["odds"][i])
                if stake < 50: continue
                bank += stake * (m["odds"][i] - 1) if outcome_win(LBL[i], m["f"]) else -stake
        rois.append((bank - 100000) / 100000)
    rois.sort()
    return sum(rois) / len(rois), rois[int(0.05 * len(rois))], rois[int(0.95 * len(rois))], sum(1 for r in rois if r > 0) / len(rois)
for l, f in STRATS:
    mean, lo, hi, pwin = boot_strategy(f)
    print(f"{l:<16} ROI medio {mean*100:>6.1f}%  [P5 {lo*100:>6.1f}% .. P95 {hi*100:>6.1f}%]  prob(ganar)={pwin*100:.0f}%")

# ---------- Calibración del modelo GLM ----------
print(f"\n{'='*78}\nCALIBRACION del modelo (¿el 67% gana ~67%?)\n{'='*78}")
buckets = defaultdict(lambda: [0, 0])
for m in MATCHES:
    for i in range(3):
        b = round(m["model"][i] * 10) / 10
        buckets[b][0] += m["model"][i]; buckets[b][1] += outcome_win(LBL[i], m["f"])
for b in sorted(buckets):
    pred, real = buckets[b]
    n = sum(1 for m in MATCHES for i in range(3) if round(m["model"][i]*10)/10 == b)
    print(f"  prob~{b*100:>3.0f}%:  predicho {pred/n*100:>4.0f}%  real {real/n*100:>4.0f}%  (n={n})")
