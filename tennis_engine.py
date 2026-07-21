#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOTOR DE TENIS — Wuru v1 (cadena de Markov jerárquica punto->juego->set->partido).
Modelo estándar de la industria (Klaassen & Magnus / Barnett & Clarke):
  input: prob de ganar punto AL SAQUE de cada jugador (pa, pb) -> prob de partido (BO3/BO5).
Los gemelos GLM (forma, superficie, fatiga, psicología) modulan pa/pb alrededor de una base Elo.
Uso como lib: match_prob(pa, pb, best_of=3). CLI demo: python3 tennis_engine.py 0.65 0.62
"""
import sys
from functools import lru_cache

# ---- juego al saque: prob de ganar un juego sirviendo con prob p por punto ----
@lru_cache(maxsize=None)
def game_prob(p):
    q = 1 - p
    # llegar a 40-0/15/30 y ganar + deuce
    win_before_deuce = p**4 * (1 + 4*q + 10*q*q)
    p_deuce = 20 * p**3 * q**3
    deuce_win = p*p / (p*p + q*q)          # ganar desde deuce (2 seguidos)
    return win_before_deuce + p_deuce * deuce_win

# ---- tiebreak: prob de ganarlo si A sirve primero (pa, pb por punto al saque) ----
@lru_cache(maxsize=None)
def tiebreak_prob(pa, pb):
    ps, pr = pa, 1 - pb                     # punto al saque propio / al resto
    # desde deuce (6-6+): se juegan pares saque+resto; ganar 2 seguidos vs perder 2
    d_win = (ps * pr) / (ps * pr + (1 - ps) * (1 - pr))
    @lru_cache(maxsize=None)
    def f(a, b):
        if a >= 7 and a - b >= 2: return 1.0
        if b >= 7 and b - a >= 2: return 0.0
        if a >= 6 and b >= 6 and a == b: return d_win
        total = a + b
        serves_a = (total == 0) or (((total + 1) // 2) % 2 == 0)  # patrón A,BB,AA,BB...
        p = pa if serves_a else (1 - pb)
        return p * f(a + 1, b) + (1 - p) * f(a, b + 1)
    return f(0, 0)

# ---- set: prob de que A gane un set (A sirve primero) ----
@lru_cache(maxsize=None)
def set_prob(pa, pb):
    ga, gb = game_prob(pa), game_prob(pb)   # prob de ganar el propio juego de saque
    @lru_cache(maxsize=None)
    def f(a, b, a_serving):
        if a == 6 and b <= 4: return 1.0
        if b == 6 and a <= 4: return 0.0
        if a == 7 or b == 7: return 1.0 if a == 7 else 0.0
        if a == 6 and b == 6: return tiebreak_prob(pa, pb)
        pwin = ga if a_serving else (1 - gb)
        return pwin * f(a + 1, b, not a_serving) + (1 - pwin) * f(a, b + 1, not a_serving)
    return f(0, 0, True)

def match_prob(pa, pb, best_of=3):
    """Prob de que A gane el partido dado pa/pb (prob de punto al saque de cada uno)."""
    s = set_prob(round(pa, 3), round(pb, 3))
    if best_of == 3:
        return s*s + 2 * s*s * (1 - s)
    # BO5
    return s**3 + 3 * s**3 * (1-s) + 6 * s**3 * (1-s)**2

def elo_to_serve_points(elo_diff, surface_adj=0.0, base=0.62):
    """Traduce diferencia de Elo (+ajuste superficie) a (pa, pb) alrededor de base 62%."""
    d = (elo_diff + surface_adj) / 400.0 * 0.055   # ~400 Elo ≈ ±5.5 pts de saque
    return min(max(base + d, 0.45), 0.80), min(max(base - d, 0.45), 0.80)

if __name__ == "__main__":
    pa, pb = float(sys.argv[1]), float(sys.argv[2])
    bo = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    print(f"pa={pa} pb={pb} BO{bo} -> P(gana A) = {match_prob(pa, pb, bo)*100:.1f}%")
