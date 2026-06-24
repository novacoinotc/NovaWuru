#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMULACION ESTOCASTICA CON GEMELOS DIGITALES: MEXICO vs COREA
Mundial 2026 - Grupo A J2 - Estadio Akron, Guadalajara - 18-jun-2026

Lee twins.json (gemelo digital biografico+atributos de los 22 jugadores) y
env.json (clima, pasto, aficion). NADA es estatico: cada uno de los N partidos
sortea:
  - Condiciones del dia: lluvia (Bernoulli), temperatura, intensidad de aficion.
  - "Dia" de cada jugador: forma del dia (los inconsistentes oscilan mas),
    temple del dia (Normal alrededor de su media con su volatilidad), efecto de
    partido grande (clutch), motivacion/animo, riesgo de lesion en el partido.
Luego corre el motor minuto a minuto (fatiga/altitud, marcador, rojas) y agrega.
"""
import json, time
import numpy as np
from collections import Counter
from multiprocessing import Pool, cpu_count

SEED = 20260618
N_SIMS = 500_000
MINUTES = 96
BASE_MEX, BASE_KOR = 1.30, 1.02   # ancla (consenso previo, pre-ajuste fino)

# ---------------------------------------------------------------------------
def role_weights(pos):
    """Pesos de contribucion (ataque, defensa, creatividad) segun posicion."""
    p = pos.lower()
    if 'portero' in p or 'gk' in p:            return (0.0, 1.0, 0.0)
    if 'central' in p:                         return (0.05, 1.0, 0.05)
    if 'lateral' in p or 'defensa' in p:       return (0.25, 0.85, 0.15)
    if 'contenc' in p or 'pivote' in p or 'defensivo' in p: return (0.30, 0.70, 0.30)
    if 'ofensiv' in p or 'mediapunta' in p or '10' in p:    return (0.85, 0.20, 0.95)
    if 'extremo' in p:                         return (0.90, 0.20, 0.70)
    if 'delantero' in p:                       return (1.00, 0.10, 0.55)
    if 'medioc' in p or 'mediocampista' in p or 'organizador' in p or '8' in p: return (0.60, 0.45, 0.85)
    return (0.5, 0.5, 0.5)

def load():
    twins = json.load(open("twins.json", encoding='utf-8'))
    env = json.load(open("env.json", encoding='utf-8'))
    return twins, env

def to_arrays(twins):
    """Convierte los 22 gemelos en arrays alineados + mascaras de equipo."""
    keys = ['skill','finishing','creativity','pace','aerial','defense','stamina_base',
            'composure_mean','composure_volatility','clutch','pressure_resistance',
            'discipline','consistency','motivation_today','emotional_state_today','injury_risk']
    A = {k: np.array([float(t.get(k, 50)) for t in twins]) for k in keys}
    # ---- Atributos fisicos / anatomia ----
    A['height']    = np.array([float(t.get('height_cm', 180)) for t in twins])
    A['pace']      = np.array([float(t.get('pace', 60)) for t in twins])
    A['top_speed'] = np.array([float(t.get('top_speed_kmh', 31)) for t in twins])
    A['durability']= np.array([float(t.get('durability', 70)) for t in twins])
    A['team'] = np.array([t['team'] for t in twins])
    wa, wd, wc = zip(*[role_weights(t['position']) for t in twins])
    A['w_att'] = np.array(wa); A['w_def'] = np.array(wd); A['w_cre'] = np.array(wc)
    A['names'] = [t['name'] for t in twins]
    A['mex'] = A['team'] == 'MEX'; A['kor'] = A['team'] == 'KOR'
    return A

# ---------------------------------------------------------------------------
def team_indices(A, mask, form, mind, mot_ratio):
    """Indices ofensivo/defensivo del equipo para esta tanda de simulaciones.
       form, mind, mot_ratio: arrays (n_players, n) con el 'dia' de cada jugador."""
    m = mask
    off_p = (0.5*A['finishing'][m,None] + 0.3*A['creativity'][m,None] + 0.2*A['skill'][m,None]) \
            * form[m] * mind[m] * mot_ratio[m]
    def_p = (0.6*A['defense'][m,None] + 0.2*A['aerial'][m,None] + 0.2*A['skill'][m,None]) \
            * form[m] * mind[m]
    att_idx = (A['w_att'][m,None] * off_p).sum(axis=0)
    cre_idx = (A['w_cre'][m,None] * off_p).sum(axis=0)
    def_idx = (A['w_def'][m,None] * def_p).sum(axis=0)
    return 0.7*att_idx + 0.3*cre_idx, def_idx

def baseline_indices(A, mask):
    """Version determinista (dia neutro) para anclar/normalizar."""
    n = 1
    ones = np.ones((A['skill'].shape[0], n))
    mot_ratio = np.ones_like(ones)
    return team_indices(A, mask, ones, ones, mot_ratio)

# ---------------------------------------------------------------------------
def worker(args):
    A, env, n, seed, base = args
    rng = np.random.default_rng(seed)
    P = A['skill'].shape[0]

    # ---- Condiciones del dia (por simulacion) ----
    rain = rng.random(n) < env['rain_probability_kickoff']
    temp = rng.normal(env['temp_c_kickoff'], 2.0, n)
    crowd = np.clip(rng.normal(env['crowd_noise'], 8, n), 0, 100)   # intensidad aficion del dia
    pitch_speed = np.where(rain, env['pitch_speed_factor'] * 1.06, env['pitch_speed_factor'])

    # ---- "Dia" de cada jugador (arrays P x n) ----
    cons = A['consistency'][:,None]
    form_z = rng.standard_normal((P, n))
    form = 1.0 + form_z * (1 - cons/100.0) * 0.30          # inconsistentes oscilan mas
    # temple del dia ~ Normal(media + empujon de clutch en partido grande, volatilidad)
    clutch_adj = (A['clutch'][:,None] - 50) * 0.10
    comp_today = rng.normal(A['composure_mean'][:,None] + clutch_adj, A['composure_volatility'][:,None])
    comp_today = np.clip(comp_today, 10, 100)
    mind = comp_today / np.clip(A['composure_mean'][:,None], 20, 100)   # ratio ~1
    # motivacion/animo del dia (pequena oscilacion)
    mot = np.clip(A['motivation_today'][:,None] + rng.normal(0, 5, (P, n)), 0, 100)
    mot_ratio = mot / np.clip(A['motivation_today'].mean(), 40, 100)
    # lesion/salida temprana: combina riesgo declarado + fragilidad (baja durabilidad)
    frailty = np.maximum(A['injury_risk'][:,None], 100 - A['durability'][:,None])
    injured = rng.random((P, n)) < (frailty/100.0) * 0.05
    form = np.where(injured, form*0.5, form)

    # ---- Indices de equipo ----
    att_mex, def_mex = team_indices(A, A['mex'], form, mind, mot_ratio)
    att_kor, def_kor = team_indices(A, A['kor'], form, mind, mot_ratio)

    # ---- Multiplicadores relativos al dia neutro (mantiene calibracion) ----
    am_mult = att_mex / base['att_mex']
    ak_mult = att_kor / base['att_kor']
    dm_ratio = base['def_mex'] / def_mex     # mejor defensa MEX => rival anota menos
    dk_ratio = base['def_kor'] / def_kor

    # ---- Condiciones -> modificadores ----
    crowd_boost = 1 + 0.0020*(crowd - 50)                 # afición: empuja a Mexico
    rain_mex = np.where(rain, 0.98, 1.0)                  # lluvia complica control local
    rain_kor = np.where(rain, 1.04, 1.0)                  # y favorece contragolpe coreano
    alt_kor = 1.0   # altitud se modela como fatiga en el motor (abajo)

    # ---- ANATOMIA: aereo en balon parado (altura+aerial de centrales y delanteros) ----
    def aerial_index(mask):
        w = (A['w_def'][mask] + A['w_att'][mask])   # zagueros y delanteros disputan el area
        h = A['height'][mask]; a = A['aerial'][mask]
        return float(np.average(0.6*(h-170) + 0.4*(a-50), weights=np.clip(w,0.05,None)))
    aer_mex = aerial_index(A['mex']); aer_kor = aerial_index(A['kor'])
    sp_mex = 0.06 * max(aer_mex - aer_kor, -8) / 6.0   # ventaja aerea => goles de balon parado
    sp_kor = 0.06 * max(aer_kor - aer_mex, -8) / 6.0

    # ---- ANATOMIA: contragolpe por velocidad punta (atacantes), potenciado en cancha mojada ----
    def pace_idx(mask):
        w = A['w_att'][mask]; return float(np.average(0.5*A['pace'][mask]+0.5*(A['top_speed'][mask]-28)*8, weights=np.clip(w,0.05,None)))
    pc_mex = pace_idx(A['mex']); pc_kor = pace_idx(A['kor'])
    wet = 1 + 0.5*rain                                  # lluvia => contragolpe mas letal
    counter_mex = 1 + 0.0015*(pc_mex - pc_kor) * wet
    counter_kor = 1 + 0.0015*(pc_kor - pc_mex) * wet

    lam_mex = BASE_MEX * am_mult * dk_ratio * crowd_boost * rain_mex * counter_mex + sp_mex
    lam_kor = BASE_KOR * ak_mult * dm_ratio * rain_kor * alt_kor * counter_kor + sp_kor
    lam_mex = np.clip(lam_mex, 0.2, 5.0); lam_kor = np.clip(lam_kor, 0.2, 5.0)

    # ---- Stamina/altitud por equipo (Mexico aclimatado, Corea sufre el ultimo tercio)
    stam_mex = (A['stamina_base'][A['mex']].mean() - 50) * 0.4 + 10   # +ventaja altura
    stam_kor = (A['stamina_base'][A['kor']].mean() - 50) * 0.4 - 9    # -penalizacion altura
    # disciplina -> riesgo de roja por equipo (jugadores de campo)
    card_mex = 100 - A['discipline'][A['mex']].mean()
    card_kor = 100 - A['discipline'][A['kor']].mean()
    card_mex *= np.where(rain.mean()>0.5, 1.1, 1.0); card_kor *= np.where(rain.mean()>0.5, 1.1, 1.0)

    # ---- Motor minuto a minuto (vectorizado) ----
    gm = np.zeros(n, np.int16); gk = np.zeros(n, np.int16)
    red_m = np.zeros(n, bool); red_k = np.zeros(n, bool)
    rm0 = lam_mex/90.0; rk0 = lam_kor/90.0
    for t in range(1, MINUTES+1):
        if t > 60:
            ph = (t-60)/36.0
            fm = 1 + (stam_mex/100)*ph*0.8 + 0.10*ph
            fk = 1 + (stam_kor/100)*ph*0.8 + 0.10*ph
        else:
            fm = fk = 1.0
        diff = gm - gk
        push_m = np.where(diff<0, 1.18, np.where(diff>0, 0.92, 1.0))
        push_k = np.where(diff>0, 1.18, np.where(diff<0, 0.92, 1.0))
        rc_m = np.where(red_m,0.72,1.0)*np.where(red_k,1.15,1.0)
        rc_k = np.where(red_k,0.72,1.0)*np.where(red_m,1.15,1.0)
        gm += (rng.random(n) < rm0*fm*push_m*rc_m).astype(np.int16)
        gk += (rng.random(n) < rk0*fk*push_k*rc_k).astype(np.int16)
        hz_m = (card_mex/100)*0.0009*(1+0.5*(diff<0))
        hz_k = (card_kor/100)*0.0009*(1+0.5*(diff>0))
        red_m |= (rng.random(n) < hz_m) & (~red_m)
        red_k |= (rng.random(n) < hz_k) & (~red_k)
    return gm, gk, red_m, red_k, rain, lam_mex, lam_kor

# ---------------------------------------------------------------------------
def main():
    t0 = time.time()
    twins, env = load()
    A = to_arrays(twins)
    base = dict(zip(['att_mex','def_mex'], baseline_indices(A, A['mex'])))
    bk = dict(zip(['att_kor','def_kor'], baseline_indices(A, A['kor'])))
    base.update(bk)
    base = {k: float(np.asarray(v).reshape(-1)[0]) for k,v in base.items()}

    print("#"*70)
    print("#  SIMULACION ESTOCASTICA CON GEMELOS DIGITALES (22 jugadores)")
    print("#  Mexico vs Corea | Mundial 2026 Grupo A J2 | Estadio Akron")
    print("#"*70)
    print(f"\n  ENTORNO (sorteado por partido):")
    print(f"   Lluvia al inicio: {env['rain_probability_kickoff']*100:.0f}%  | Temp ~{env['temp_c_kickoff']:.0f}C  | "
          f"Humedad {env['humidity_pct']:.0f}%  | Viento {env['wind_kmh']:.0f}km/h")
    print(f"   Pasto: {env['pitch_type']} ({env['pitch_condition']}) factor {env['pitch_speed_factor']:.2f}")
    print(f"   Aforo {env['stadium_capacity']:,} | asistencia ~{env['expected_attendance']:,} | "
          f"aficion local {env['home_support_pct']*100:.0f}% | coreanos ~{env['korean_fans_estimate']:,}")
    print(f"   Hostilidad {env['crowd_hostility']}/100 | ruido {env['crowd_noise']}/100")

    cores = max(cpu_count()-1, 1)
    chunk = N_SIMS // cores
    tasks = [(A, env, chunk, SEED+i, base) for i in range(cores)]
    with Pool(cores) as pool:
        res = pool.map(worker, tasks)
    gm = np.concatenate([r[0] for r in res]); gk = np.concatenate([r[1] for r in res])
    rm = np.concatenate([r[2] for r in res]); rk = np.concatenate([r[3] for r in res])
    rain = np.concatenate([r[4] for r in res])
    lmx = np.concatenate([r[5] for r in res]); lko = np.concatenate([r[6] for r in res])
    n = len(gm)

    mw,dr,kw = np.mean(gm>gk), np.mean(gm==gk), np.mean(gm<gk)
    tot = gm+gk
    print(f"\n{'='*68}")
    print(f"  RESULTADO ({n:,} partidos, {cores} nucleos)")
    print(f"  lambda promedio:  MEX {lmx.mean():.2f} (sd {lmx.std():.2f})  -  KOR {lko.mean():.2f} (sd {lko.std():.2f})")
    print(f"{'='*68}")
    print(f"  Gana MEXICO : {mw*100:6.2f}%   (cuota justa {1/mw:.2f})")
    print(f"  EMPATE      : {dr*100:6.2f}%   (cuota justa {1/dr:.2f})")
    print(f"  Gana COREA  : {kw*100:6.2f}%   (cuota justa {1/kw:.2f})")
    print(f"  Mexico NO pierde: {(mw+dr)*100:.1f}%   |   Corea NO pierde: {(kw+dr)*100:.1f}%")
    print(f"\n  Goles esperados:  MEX {gm.mean():.2f}  -  KOR {gk.mean():.2f}  (total {tot.mean():.2f})")
    print(f"  Over 2.5: {np.mean(tot>=3)*100:.1f}%  Under 2.5: {np.mean(tot<=2)*100:.1f}%  BTTS: {np.mean((gm>=1)&(gk>=1))*100:.1f}%")
    print(f"  Roja MEX: {rm.mean()*100:.1f}%  Roja KOR: {rk.mean()*100:.1f}%  (alguna {np.mean(rm|rk)*100:.1f}%)")
    print(f"\n  Condicional segun el dia:")
    if rain.sum()>0 and (~rain).sum()>0:
        print(f"   CON lluvia ({rain.mean()*100:.0f}% de partidos): MEX {np.mean(gm[rain]>gk[rain])*100:.1f}% | "
              f"E {np.mean(gm[rain]==gk[rain])*100:.1f}% | KOR {np.mean(gm[rain]<gk[rain])*100:.1f}%")
        print(f"   SIN lluvia:                       MEX {np.mean(gm[~rain]>gk[~rain])*100:.1f}% | "
              f"E {np.mean(gm[~rain]==gk[~rain])*100:.1f}% | KOR {np.mean(gm[~rain]<gk[~rain])*100:.1f}%")
    print(f"\n  Marcadores mas probables:")
    for (a,b),c in Counter(zip(gm.tolist(),gk.tolist())).most_common(8):
        print(f"      MEX {a}-{b} KOR : {c/n*100:5.2f}%")
    print(f"\n  Tiempo: {time.time()-t0:.2f}s")
    print("#"*70)

if __name__ == "__main__":
    main()
