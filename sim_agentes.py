#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMULACION AGENTE-POR-JUGADOR: MEXICO vs COREA DEL SUR
Mundial 2026 - Grupo A J2 - Estadio Akron, Guadalajara - 18-jun-2026

Lee player_minds.json (22 jugadores, 1 agente IA por jugador que "penso" como el
y devolvio su estado mental + modificadores). Convierte esas mentes en parametros
de equipo y simula el partido MINUTO A MINUTO 100,000 veces:
 - definicion/temple modulados por presion, nervios y confianza (efecto "choke")
 - fatiga por altitud en el ultimo tercio (segun stamina_altitude de cada equipo)
 - conducta segun marcador (el que pierde arriesga; el rival contragolpea)
 - rojas (arbitro estricto Tejera + riesgo emocional) que cambian el partido
 - factores situacionales de la investigacion (altura, lluvia, afición, arbitro)
"""
import json, sys, time
import numpy as np
from collections import Counter
from multiprocessing import Pool, cpu_count

SEED = 20260618
N_SIMS = 100_000
MINUTES = 96            # 90 + ~6 de anadido
MINDS_FILE = "player_minds.json"

# Lambdas base de consenso (del modelo estadistico previo de 5.5M sims)
BASE_MEX, BASE_KOR = 1.22, 0.99

# ---- Factores situacionales (de la investigacion, favorecen +MEX / +KOR a xG) ----
SIT = dict(
    altitude_mex=+0.04, altitude_kor=-0.04,   # altura, mitigada (Corea aclimatada 2 sem)
    rain_kor=+0.03, rain_mex=-0.02,            # cancha mojada ayuda al contragolpe coreano
    crowd_mex=+0.10,                           # aficion/anfitrion (impacto fuerte)
    h2h_mex=+0.03,                             # ventaja psicologica historica en Mundiales
    korea_distraction_kor=-0.03,               # polemica interna Son/prensa
    montes_out_kor=+0.05,                      # zaga mexicana debilitada (Montes suspendido)
)

FORWARDS = ('Delantero', 'extremo', 'Extremo', 'Mediapunta', 'ofensivo', 'Delantero/extremo')
BACKS = ('Portero', 'Lateral', 'Central')

def m(x): return 1.0 + x/100.0   # convierte % a multiplicador

def load_minds(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def is_attacker(pos):  return any(k in pos for k in FORWARDS)
def is_defender(pos):  return any(k in pos for k in BACKS)

def team_params(minds, team):
    pl = [p for p in minds if p['team'] == team]
    atk = [p for p in pl if is_attacker(p['position'])]
    dfn = [p for p in pl if is_defender(p['position'])]
    if not atk: atk = pl
    if not dfn: dfn = pl
    def avg(group, key): return float(np.mean([g[key] for g in group]))

    # Multiplicador de ataque: definicion + creatividad + temple de los de arriba,
    # penalizado por el "choke" (presion+nervios altos bajan rendimiento)
    fin = avg(atk, 'finishing_mod'); cre = avg(atk, 'creativity_mod'); comp = avg(atk, 'composure_mod')
    pressure = avg(pl, 'pressure'); nerves = avg(pl, 'nerves'); conf = avg(pl, 'confidence')
    choke = -((pressure + nerves)/2 - 50) * 0.12        # >50 presion/nervios => penaliza
    att_mult = m((fin + cre + comp)/3 + choke*0.5 + (conf-50)*0.06)

    # Multiplicador de solidez defensiva (menor => concede menos). defense_mod alto = mejor defensa.
    dmod = avg(dfn, 'defense_mod'); dcomp = avg(dfn, 'composure_mod')
    def_solidity = m(-(dmod + dcomp)/2 - choke*0.3)     # mejor defensa => multiplicador < 1

    # Resistencia / altitud (afecta ultimo tercio)
    stamina = avg(pl, 'stamina_altitude_mod')
    # Riesgo de roja del equipo (promedio card_risk de campo, sube con arbitro estricto)
    card = avg([p for p in pl if 'Portero' not in p['position']], 'card_risk')

    return dict(att_mult=att_mult, def_solidity=def_solidity, stamina=stamina,
                card=card, pressure=pressure, nerves=nerves, conf=conf,
                motivation=avg(pl,'motivation'), focus=avg(pl,'focus'),
                star_finish=max(p['finishing_mod'] for p in atk))

def build_lambdas(minds):
    mx = team_params(minds, 'MEX'); ko = team_params(minds, 'KOR')
    # lambda efectivo = base * ataque_propio * (debilidad_defensiva_rival) * factores situacionales
    sit_mex = (1 + SIT['altitude_mex'] + SIT['crowd_mex'] + SIT['h2h_mex'] + SIT['rain_mex'])
    sit_kor = (1 + SIT['altitude_kor'] + SIT['rain_kor'] + SIT['korea_distraction_kor'] + SIT['montes_out_kor'])
    lam_mex = BASE_MEX * mx['att_mult'] * ko['def_solidity'] * sit_mex
    lam_kor = BASE_KOR * ko['att_mult'] * mx['def_solidity'] * sit_kor
    return lam_mex, lam_kor, mx, ko

# ---------------------------------------------------------------------------
# Motor minuto a minuto, vectorizado sobre N simulaciones
# ---------------------------------------------------------------------------
def simulate_chunk(args):
    lam_mex, lam_kor, stam_mex, stam_kor, card_mex, card_kor, n, seed = args
    rng = np.random.default_rng(seed)
    gm = np.zeros(n, dtype=np.int16); gk = np.zeros(n, dtype=np.int16)
    red_mex = np.zeros(n, dtype=bool); red_kor = np.zeros(n, dtype=bool)
    # tasa base por minuto
    rm0 = lam_mex / 90.0; rk0 = lam_kor / 90.0
    for t in range(1, MINUTES + 1):
        # fatiga/altitud en el ultimo tercio (min 60+): escala segun stamina relativa
        if t > 60:
            ph = (t - 60) / 36.0
            fm = 1.0 + (stam_mex/100.0) * ph * 0.8 + 0.10*ph   # cansancio general sube tasas
            fk = 1.0 + (stam_kor/100.0) * ph * 0.8 + 0.10*ph
        else:
            fm = fk = 1.0
        # conducta segun marcador: el que pierde arriesga (+ataque, +concede)
        diff = gm - gk
        push_mex = np.where(diff < 0, 1.18, np.where(diff > 0, 0.92, 1.0))
        push_kor = np.where(diff > 0, 1.18, np.where(diff < 0, 0.92, 1.0))
        # efecto de rojas
        rc_mex = np.where(red_mex, 0.72, 1.0) * np.where(red_kor, 1.15, 1.0)
        rc_kor = np.where(red_kor, 0.72, 1.0) * np.where(red_mex, 1.15, 1.0)

        rate_m = rm0 * fm * push_mex * rc_mex
        rate_k = rk0 * fk * push_kor * rc_kor
        gm += (rng.random(n) < rate_m).astype(np.int16)
        gk += (rng.random(n) < rate_k).astype(np.int16)

        # tarjetas rojas (raras): hazard por minuto ~ card_risk del equipo / escala
        hz_m = (card_mex/100.0) * 0.0009 * (1 + 0.5*(diff < 0))
        hz_k = (card_kor/100.0) * 0.0009 * (1 + 0.5*(diff > 0))
        new_rm = (rng.random(n) < hz_m) & (~red_mex)
        new_rk = (rng.random(n) < hz_k) & (~red_kor)
        red_mex |= new_rm; red_kor |= new_rk
    return gm, gk, red_mex, red_kor

def run(lam_mex, lam_kor, mx, ko, n=N_SIMS):
    cores = max(cpu_count() - 1, 1)
    chunk = n // cores
    tasks = [(lam_mex, lam_kor, mx['stamina'], ko['stamina'], mx['card'], ko['card'],
              chunk, SEED + i) for i in range(cores)]
    with Pool(cores) as pool:
        res = pool.map(simulate_chunk, tasks)
    gm = np.concatenate([r[0] for r in res]); gk = np.concatenate([r[1] for r in res])
    rm = np.concatenate([r[2] for r in res]); rk = np.concatenate([r[3] for r in res])
    return gm, gk, rm, rk, cores

def report(gm, gk, rm, rk, cores, lam_mex, lam_kor):
    n = len(gm)
    mw, dr, kw = np.mean(gm>gk), np.mean(gm==gk), np.mean(gm<gk)
    print(f"\n{'='*66}")
    print(f"  RESULTADO SIMULACION AGENTE-POR-JUGADOR ({n:,} partidos, {cores} nucleos)")
    print(f"  lambda efectivo:  MEX {lam_mex:.2f}  -  KOR {lam_kor:.2f}")
    print(f"{'='*66}")
    print(f"  Gana MEXICO : {mw*100:6.2f}%   (cuota justa {1/mw:.2f})")
    print(f"  EMPATE      : {dr*100:6.2f}%   (cuota justa {1/dr:.2f})")
    print(f"  Gana COREA  : {kw*100:6.2f}%   (cuota justa {1/kw:.2f})")
    print(f"  Mexico NO pierde: {(mw+dr)*100:.1f}%   |   Corea NO pierde: {(kw+dr)*100:.1f}%")
    tot = gm+gk
    print(f"\n  Goles esperados:  MEX {gm.mean():.2f}  -  KOR {gk.mean():.2f}  (total {tot.mean():.2f})")
    print(f"  Over 2.5: {np.mean(tot>=3)*100:.1f}%   Under 2.5: {np.mean(tot<=2)*100:.1f}%   BTTS: {np.mean((gm>=1)&(gk>=1))*100:.1f}%")
    print(f"  Roja a MEX: {rm.mean()*100:.1f}%   Roja a KOR: {rk.mean()*100:.1f}%   (alguna roja: {np.mean(rm|rk)*100:.1f}%)")
    print(f"\n  Marcadores mas probables:")
    for (a,b),c in Counter(zip(gm.tolist(),gk.tolist())).most_common(8):
        print(f"      MEX {a}-{b} KOR : {c/n*100:5.2f}%")
    return dict(mw=mw, dr=dr, kw=kw)

def main():
    t0 = time.time()
    minds = load_minds(MINDS_FILE)
    print("#"*68)
    print("#  SIMULACION CON 1 AGENTE IA POR JUGADOR (22 mentes)")
    print("#  Mexico vs Corea | Mundial 2026 Grupo A J2 | Estadio Akron")
    print("#"*68)
    lam_mex, lam_kor, mx, ko = build_lambdas(minds)

    print(f"\n  ESTADO MENTAL AGREGADO POR EQUIPO (0-100):")
    for name, tp in (('MEXICO', mx), ('COREA', ko)):
        print(f"   {name:7}: presion {tp['pressure']:.0f} | nervios {tp['nerves']:.0f} | "
              f"confianza {tp['conf']:.0f} | motivacion {tp['motivation']:.0f} | foco {tp['focus']:.0f}")
        print(f"            mult.ataque {tp['att_mult']:.3f} | solidez def {tp['def_solidity']:.3f} | "
              f"stamina/altitud {tp['stamina']:+.1f} | riesgo tarjeta {tp['card']:.0f}")

    gm, gk, rm, rk, cores = run(lam_mex, lam_kor, mx, ko)
    report(gm, gk, rm, rk, cores, lam_mex, lam_kor)
    print(f"\n  Tiempo: {time.time()-t0:.2f}s")
    print("#"*68)

if __name__ == "__main__":
    main()
