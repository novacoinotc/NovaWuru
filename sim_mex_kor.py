#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulacion Monte Carlo: MEXICO vs COREA DEL SUR
Mundial 2026 - Grupo A - Jornada 2 - Estadio Akron, Guadalajara - 18 jun 2026

Metodologia (basada en literatura de analytics: Maher 1982, Dixon-Coles 1997,
Karlis-Ntzoufras 2003, World Football Elo, de-vig de cuotas):
 - Varios modelos de goles esperados (lambda) por equipo.
 - Poisson bivariada (componente compartido) para correlacionar goles.
 - Correccion Dixon-Coles para marcadores bajos (mas empates 0-0, 1-1).
 - Consenso = promedio de modelos + mega-ensamble de 1,000,000 con multiprocessing.
"""

import numpy as np
from math import exp, factorial
from multiprocessing import Pool, cpu_count
from collections import Counter
import time

RNG_SEED = 20260618
N_SIMS = 100_000          # por modelo (lo que pidio el usuario)
N_ENSEMBLE = 1_000_000    # mega-corrida de consenso usando todos los nucleos
DC_RHO = -0.08            # parametro Dixon-Coles (mas masa en 0-0 y 1-1)
BIV_L3 = 0.10             # componente compartido (correlacion entre goles)

# ----------------------------------------------------------------------------
# DEFINICION DE MODELOS  (lambda = goles esperados de cada equipo)
# Derivados de la investigacion. MEX = local.
# ----------------------------------------------------------------------------
# Justificacion de cada par de lambdas en los comentarios.
MODELS = {
    # Fuerza ataque/defensa ajustada por calidad de rival + ventaja local (x1.15)
    # MEX att~1.04, def fuerte; KOR att~1.08, def media. lambda_mex=1.30*1.04*0.77*1.15
    "Dixon-Coles (forma/xG)": dict(l_mex=1.20, l_kor=0.97),
    # Elo: MEX 1805 +75 local = 1880 vs KOR 1740 -> dr=140 -> supremacia 0.35 gol,
    # base total 2.2 baja. lambda_mex=1.1+0.175 ; lambda_kor=1.1-0.175
    "Elo (1880 vs 1740)":     dict(l_mex=1.28, l_kor=0.93),
    # Calibrado para reproducir el mercado de-vig (~48/27/25)
    "Mercado (cuotas de-vig)": dict(l_mex=1.24, l_kor=1.02),
    # Penaliza a MEX por bajas (Malagon portero #1 fuera, Montes suspendido en CB)
    # y a KOR un poco por perder 2 mediocampistas defensivos
    "Ajustado por bajas":     dict(l_mex=1.15, l_kor=1.05),
}

# ----------------------------------------------------------------------------
# Simulacion vectorizada: Poisson bivariada con correccion Dixon-Coles
# ----------------------------------------------------------------------------
def simulate(l_mex, l_kor, n, rho=DC_RHO, l3=BIV_L3, seed=RNG_SEED):
    rng = np.random.default_rng(seed)
    # Poisson bivariada: X1,X2 propios + X3 compartido -> correlacion = l3
    l3e = min(l3, l_mex - 0.01, l_kor - 0.01)
    x1 = rng.poisson(max(l_mex - l3e, 0.01), n)
    x2 = rng.poisson(max(l_kor - l3e, 0.01), n)
    x3 = rng.poisson(max(l3e, 0.0), n)
    gm = x1 + x3   # goles Mexico
    gk = x2 + x3   # goles Corea

    # Correccion Dixon-Coles (re-muestreo de probabilidad sobre marcadores bajos):
    # aplicamos un factor de aceptacion/rechazo a los 4 marcadores bajos.
    tau = np.ones(n)
    m00 = (gm == 0) & (gk == 0); tau[m00] = 1 - l_mex * l_kor * rho
    m10 = (gm == 1) & (gk == 0); tau[m10] = 1 + l_kor * rho
    m01 = (gm == 0) & (gk == 1); tau[m01] = 1 + l_mex * rho
    m11 = (gm == 1) & (gk == 1); tau[m11] = 1 - rho
    # tau>1 => reforzar esos marcadores. Re-muestreo por pesos.
    w = tau / tau.sum()
    idx = rng.choice(n, size=n, replace=True, p=w)
    return gm[idx], gk[idx]


def aggregate(gm, gk, label):
    n = len(gm)
    mex_w = np.mean(gm > gk)
    draw  = np.mean(gm == gk)
    kor_w = np.mean(gm < gk)
    total = gm + gk
    over25 = np.mean(total >= 3)
    btts  = np.mean((gm >= 1) & (gk >= 1))
    cs_mex = np.mean(gk == 0)   # porteria a cero MEX
    cs_kor = np.mean(gm == 0)   # porteria a cero KOR
    # marcadores mas probables
    scores = Counter(zip(gm.tolist(), gk.tolist()))
    top = scores.most_common(8)
    return dict(label=label, n=n, mex_w=mex_w, draw=draw, kor_w=kor_w,
                eg_mex=gm.mean(), eg_kor=gk.mean(), eg_tot=total.mean(),
                over25=over25, under25=1-over25, btts=btts,
                cs_mex=cs_mex, cs_kor=cs_kor, top=top)


def fair_odds(p):
    return 1/p if p > 0 else float('inf')


def print_report(r):
    print(f"\n  {'='*64}")
    print(f"  MODELO: {r['label']}   (n={r['n']:,})")
    print(f"  {'-'*64}")
    print(f"  Gana MEXICO : {r['mex_w']*100:6.2f}%   (cuota justa {fair_odds(r['mex_w']):.2f})")
    print(f"  EMPATE      : {r['draw']*100:6.2f}%   (cuota justa {fair_odds(r['draw']):.2f})")
    print(f"  Gana COREA  : {r['kor_w']*100:6.2f}%   (cuota justa {fair_odds(r['kor_w']):.2f})")
    print(f"  Goles esperados:  MEX {r['eg_mex']:.2f}  -  KOR {r['eg_kor']:.2f}   (total {r['eg_tot']:.2f})")
    print(f"  Over 2.5: {r['over25']*100:5.2f}%   Under 2.5: {r['under25']*100:5.2f}%   BTTS(ambos anotan): {r['btts']*100:5.2f}%")
    print(f"  Porteria a cero:  MEX {r['cs_mex']*100:5.2f}%   KOR {r['cs_kor']*100:5.2f}%")
    print(f"  Marcadores mas probables:")
    for (a, b), c in r['top']:
        print(f"      MEX {a}-{b} KOR : {c/r['n']*100:5.2f}%")


# ----------------------------------------------------------------------------
# Mega-ensamble con multiprocessing (consenso de los 4 modelos)
# ----------------------------------------------------------------------------
def _worker(args):
    l_mex, l_kor, n, seed = args
    gm, gk = simulate(l_mex, l_kor, n, seed=seed)
    return gm, gk


def run_ensemble(models, total_n):
    cores = max(cpu_count() - 1, 1)
    per_model = total_n // len(models)
    chunk = per_model // cores
    tasks = []
    s = RNG_SEED
    for m in models.values():
        for c in range(cores):
            s += 1
            tasks.append((m['l_mex'], m['l_kor'], chunk, s))
    with Pool(cores) as pool:
        results = pool.map(_worker, tasks)
    gm = np.concatenate([r[0] for r in results])
    gk = np.concatenate([r[1] for r in results])
    return gm, gk, cores


# ----------------------------------------------------------------------------
def main():
    t0 = time.time()
    print("#"*70)
    print("#  MONTE CARLO: MEXICO vs COREA DEL SUR")
    print("#  Mundial 2026 | Grupo A J2 | Estadio Akron, Guadalajara | 18-jun-2026")
    print("#"*70)

    reports = []
    for label, m in MODELS.items():
        gm, gk = simulate(m['l_mex'], m['l_kor'], N_SIMS)
        r = aggregate(gm, gk, label)
        reports.append(r)
        print_report(r)

    # Mega-ensamble consenso
    print(f"\n  {'#'*64}")
    print(f"  CONSENSO (mega-ensamble {N_ENSEMBLE:,} simulaciones, multiprocessing)")
    gm, gk, cores = run_ensemble(MODELS, N_ENSEMBLE)
    rc = aggregate(gm, gk, f"CONSENSO ENSAMBLE ({cores} nucleos)")
    print_report(rc)

    # Promedio simple de los 4 modelos (otra vista de consenso)
    avg = dict(
        mex_w=np.mean([r['mex_w'] for r in reports]),
        draw=np.mean([r['draw'] for r in reports]),
        kor_w=np.mean([r['kor_w'] for r in reports]),
    )
    print(f"\n  {'-'*64}")
    print(f"  PROMEDIO SIMPLE DE LOS 4 MODELOS:")
    print(f"      Gana MEXICO {avg['mex_w']*100:.2f}%  |  EMPATE {avg['draw']*100:.2f}%  |  Gana COREA {avg['kor_w']*100:.2f}%")

    print(f"\n  Tiempo total: {time.time()-t0:.2f}s")
    print("#"*70)


if __name__ == "__main__":
    main()
