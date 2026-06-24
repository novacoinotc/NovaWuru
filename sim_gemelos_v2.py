#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MOTOR v2 — MEXICO vs COREA — calibrado tras el resultado real (MEX 1-0, 18-jun-2026)

MEJORAS sobre v1 (motivadas por el partido real):
 1. GOLES MÁS BAJOS: total ~2.2 (v1 daba 2.7; real fue 1). Separa CREACIÓN (xG) de CONVERSIÓN.
 2. CAPA DE PORTERO: el partido lo decidió el portero (error de Kim, dobles atajadas de Rangel).
    Cada GK tiene un rendimiento del día (Normal con volatilidad) que multiplica los goles rivales,
    capturando tanto noches heroicas como errores.
 3. CREACIÓN vs CONVERSIÓN: Corea es más de posesión (crea), México más clínico (convierte) + afición.
 4. ALTITUD SUAVIZADA → reemplazada por FATIGA basada en DISTANCIA REAL recorrida (capa física FIFA/Sofascore).
    Guadalajara (1,566 m) solo encarece un poco el esfuerzo coreano; ya no hay "desplome por altura".
 5. INCERTIDUMBRE DE ALINEACIÓN: Aguirre rota (Romo entró y marcó; Mora no jugó) → ruido en el XI.
"""
import json, time
import numpy as np
from collections import Counter
from multiprocessing import Pool, cpu_count

SEED = 20260619
N_SIMS = 500_000
MINUTES = 96
# Creación de ocasiones base (xG-like). México por encima (mejor equipo: Elo 1805 vs 1740), total ~2.2
BASE_MEX, BASE_KOR = 1.34, 0.92
NOMINAL_DIST = 115.0   # distancia de equipo "nominal" (km) para normalizar esfuerzo
ALT_COST_KOR = 1.03    # la altitud encarece ~3% el esfuerzo coreano (suave, no desplome)

def role_weights(pos):
    p = pos.lower()
    if 'portero' in p or 'gk' in p:            return (0.0, 1.0, 0.0)
    if 'central' in p:                         return (0.05, 1.0, 0.05)
    if 'lateral' in p or 'defensa' in p:       return (0.25, 0.85, 0.15)
    if 'contenc' in p or 'pivote' in p or 'defensivo' in p: return (0.30, 0.70, 0.30)
    if 'ofensiv' in p or 'mediapunta' in p or '10' in p:    return (0.85, 0.20, 0.95)
    if 'extremo' in p:                         return (0.90, 0.20, 0.70)
    if 'delantero' in p:                       return (1.00, 0.10, 0.55)
    if 'medioc' in p or 'organizador' in p or '8' in p:     return (0.60, 0.45, 0.85)
    return (0.5, 0.5, 0.5)

def load():
    return json.load(open("twins.json", encoding='utf-8')), json.load(open("env.json", encoding='utf-8'))

def to_arrays(twins):
    keys = ['skill','finishing','creativity','pace','aerial','defense','stamina_base',
            'composure_mean','composure_volatility','clutch','pressure_resistance',
            'discipline','consistency','motivation_today','emotional_state_today','injury_risk']
    A = {k: np.array([float(t.get(k, 50)) for t in twins]) for k in keys}
    A['height']    = np.array([float(t.get('height_cm', 180)) for t in twins])
    A['pace_phys'] = np.array([float(t.get('pace', 60)) for t in twins])
    A['top_speed'] = np.array([float(t.get('top_speed_kmh', 31)) for t in twins])
    A['durability']= np.array([float(t.get('durability', 70)) for t in twins])
    A['distance']  = np.array([float(t.get('distance_km', 10)) for t in twins])   # capa física real
    A['team'] = np.array([t['team'] for t in twins])
    wa, wd, wc = zip(*[role_weights(t['position']) for t in twins])
    A['w_att'] = np.array(wa); A['w_def'] = np.array(wd); A['w_cre'] = np.array(wc)
    A['is_gk'] = np.array(['portero' in t['position'].lower() or 'gk' in t['position'].lower() for t in twins])
    A['mex'] = A['team'] == 'MEX'; A['kor'] = A['team'] == 'KOR'
    return A

def team_create(A, mask, form, mind, mot):
    m = mask
    off = (0.5*A['finishing'][m,None] + 0.3*A['creativity'][m,None] + 0.2*A['skill'][m,None]) * form[m]*mind[m]*mot[m]
    att = (A['w_att'][m,None]*off).sum(0); cre = (A['w_cre'][m,None]*off).sum(0)
    return 0.7*att + 0.3*cre

def team_def(A, mask, form, mind):
    m = mask
    dfn = (0.6*A['defense'][m,None] + 0.2*A['aerial'][m,None] + 0.2*A['skill'][m,None]) * form[m]*mind[m]
    return (A['w_def'][m,None]*dfn).sum(0)

def baseline(A):
    P=A['skill'].shape[0]; o=np.ones((P,1))
    return dict(cm=float(team_create(A,A['mex'],o,o,o)[0]), ck=float(team_create(A,A['kor'],o,o,o)[0]),
                dm=float(team_def(A,A['mex'],o,o)[0]),    dk=float(team_def(A,A['kor'],o,o)[0]))

def gk_index(A, mask):
    g = mask & A['is_gk']
    if g.sum()==0: return 72.0, 12.0
    return float(0.7*A['skill'][g].mean()+0.3*A['composure_mean'][g].mean()), float(A['composure_volatility'][g].mean()+8)

def worker(args):
    A, env, n, seed, base = args
    rng = np.random.default_rng(seed)
    P = A['skill'].shape[0]

    # Condiciones del día
    rain = rng.random(n) < env['rain_probability_kickoff']
    crowd = np.clip(rng.normal(env['crowd_noise'], 8, n), 0, 100)

    # "Día" de cada jugador (+ incertidumbre de alineación: ruido extra)
    cons = A['consistency'][:,None]
    form = 1.0 + rng.standard_normal((P,n)) * (1-cons/100.0) * 0.30
    form *= (1 + rng.normal(0, 0.04, (P,n)))                      # rotación/incertidumbre XI
    comp = np.clip(rng.normal(A['composure_mean'][:,None] + (A['clutch'][:,None]-50)*0.10,
                              A['composure_volatility'][:,None]), 10, 100)
    mind = comp / np.clip(A['composure_mean'][:,None], 20, 100)
    mot = np.clip(A['motivation_today'][:,None] + rng.normal(0,5,(P,n)), 0,100) / np.clip(A['motivation_today'].mean(),40,100)
    frail = np.maximum(A['injury_risk'][:,None], 100-A['durability'][:,None])
    form = np.where(rng.random((P,n)) < frail/100.0*0.05, form*0.5, form)

    # CREACIÓN de ocasiones (xG) y DEFENSA
    cre_mex = team_create(A,A['mex'],form,mind,mot); cre_kor = team_create(A,A['kor'],form,mind,mot)
    def_mex = team_def(A,A['mex'],form,mind);        def_kor = team_def(A,A['kor'],form,mind)
    cm = cre_mex/base['cm']; ck = cre_kor/base['ck']
    dmr = base['dm']/def_mex; dkr = base['dk']/def_kor

    # ESTILO: Corea algo más de posesión (crea), México más vertical/clínico. Leve, sin sobreajustar a 1 partido.
    style_mex, style_kor = 1.00, 1.02

    # CONVERSIÓN (finishing del día de los atacantes)
    fin_mex = np.clip(((A['finishing'][A['mex']][:,None]*form[A['mex']]).mean(0))/75.0, 0.85,1.2)
    fin_kor = np.clip(((A['finishing'][A['kor']][:,None]*form[A['kor']]).mean(0))/75.0, 0.85,1.2)

    # CAPA DE PORTERO: rendimiento del día del GK rival multiplica tus goles
    sk_mex,vol_mex = gk_index(A,A['mex']); sk_kor,vol_kor = gk_index(A,A['kor'])
    gkperf_mex = rng.normal(sk_mex, vol_mex, n); gkperf_kor = rng.normal(sk_kor, vol_kor, n)
    gkfac_for_mex = np.clip(1 + (72 - gkperf_kor)/90.0, 0.75, 1.30)   # gol MEX sube si GK KOR falla
    gkfac_for_kor = np.clip(1 + (72 - gkperf_mex)/90.0, 0.75, 1.30)

    # Aéreo (balón parado por altura) y contragolpe por velocidad
    def aerial(mask):
        w=A['w_def'][mask]+A['w_att'][mask]
        return float(np.average(0.6*(A['height'][mask]-170)+0.4*(A['aerial'][mask]-50), weights=np.clip(w,0.05,None)))
    aer_mex,aer_kor = aerial(A['mex']), aerial(A['kor'])
    sp_mex = 0.05*max(aer_mex-aer_kor,-8)/6.0; sp_kor = 0.05*max(aer_kor-aer_mex,-8)/6.0
    def pace_idx(mask):
        w=A['w_att'][mask]; return float(np.average(0.5*A['pace_phys'][mask]+0.5*(A['top_speed'][mask]-28)*8, weights=np.clip(w,0.05,None)))
    pc_mex,pc_kor = pace_idx(A['mex']),pace_idx(A['kor'])
    wet=1+0.5*rain
    counter_mex=1+0.0013*(pc_mex-pc_kor)*wet; counter_kor=1+0.0013*(pc_kor-pc_mex)*wet
    crowd_boost=1+0.0020*(crowd-50); rain_mex=np.where(rain,0.98,1.0); rain_kor=np.where(rain,1.04,1.0)

    lam_mex = BASE_MEX*cm*dkr*style_mex*fin_mex*gkfac_for_mex*crowd_boost*rain_mex*counter_mex + sp_mex
    lam_kor = BASE_KOR*ck*dmr*style_kor*fin_kor*gkfac_for_kor*rain_kor*counter_kor + sp_kor
    lam_mex=np.clip(lam_mex,0.15,5.0); lam_kor=np.clip(lam_kor,0.15,5.0)

    # FATIGA por DISTANCIA REAL (reemplaza el desplome por altura)
    dist_mex = A['distance'][A['mex']].sum(); dist_kor = A['distance'][A['kor']].sum()*ALT_COST_KOR
    eff_mex = dist_mex/NOMINAL_DIST; eff_kor = dist_kor/NOMINAL_DIST
    stam_mex = (A['stamina_base'][A['mex']].mean()-50)*0.4 + (1-eff_mex)*22
    stam_kor = (A['stamina_base'][A['kor']].mean()-50)*0.4 + (1-eff_kor)*22
    card_mex = 100-A['discipline'][A['mex']].mean(); card_kor = 100-A['discipline'][A['kor']].mean()

    # Motor minuto a minuto
    gm=np.zeros(n,np.int16); gk=np.zeros(n,np.int16); rmx=np.zeros(n,bool); rkr=np.zeros(n,bool)
    rm0=lam_mex/90.0; rk0=lam_kor/90.0
    for t in range(1,MINUTES+1):
        if t>60:
            ph=(t-60)/36.0; fm=1+(stam_mex/100)*ph*0.8+0.10*ph; fk=1+(stam_kor/100)*ph*0.8+0.10*ph
        else: fm=fk=1.0
        diff=gm-gk
        pm=np.where(diff<0,1.18,np.where(diff>0,0.92,1.0)); pk=np.where(diff>0,1.18,np.where(diff<0,0.92,1.0))
        rcm=np.where(rmx,0.72,1.0)*np.where(rkr,1.15,1.0); rck=np.where(rkr,0.72,1.0)*np.where(rmx,1.15,1.0)
        gm+=(rng.random(n)<rm0*fm*pm*rcm).astype(np.int16); gk+=(rng.random(n)<rk0*fk*pk*rck).astype(np.int16)
        hm=(card_mex/100)*0.0009*(1+0.5*(diff<0)); hk=(card_kor/100)*0.0009*(1+0.5*(diff>0))
        rmx|=(rng.random(n)<hm)&(~rmx); rkr|=(rng.random(n)<hk)&(~rkr)
    return gm,gk,rmx,rkr,rain,lam_mex,lam_kor

def main():
    t0=time.time(); tw,env=load(); A=to_arrays(tw); base=baseline(A)
    print("#"*70); print("#  MOTOR v2 (calibrado tras MEX 1-0 COREA) — gemelos + física + portero"); print("#"*70)
    cores=max(cpu_count()-1,1); chunk=N_SIMS//cores
    with Pool(cores) as pool:
        res=pool.map(worker,[(A,env,chunk,SEED+i,base) for i in range(cores)])
    gm=np.concatenate([r[0] for r in res]); gk=np.concatenate([r[1] for r in res])
    rm=np.concatenate([r[2] for r in res]); rk=np.concatenate([r[3] for r in res])
    rain=np.concatenate([r[4] for r in res]); lmx=np.concatenate([r[5] for r in res]); lko=np.concatenate([r[6] for r in res])
    n=len(gm); mw,dr,kw=np.mean(gm>gk),np.mean(gm==gk),np.mean(gm<gk); tot=gm+gk
    print(f"\n  lambda promedio:  MEX {lmx.mean():.2f}  KOR {lko.mean():.2f}  (total {lmx.mean()+lko.mean():.2f})")
    print(f"  Gana MEXICO : {mw*100:6.2f}%   (cuota justa {1/mw:.2f})")
    print(f"  EMPATE      : {dr*100:6.2f}%   (cuota justa {1/dr:.2f})")
    print(f"  Gana COREA  : {kw*100:6.2f}%   (cuota justa {1/kw:.2f})")
    print(f"  Mexico NO pierde: {(mw+dr)*100:.1f}%")
    print(f"  Goles: MEX {gm.mean():.2f} - KOR {gk.mean():.2f} (total {tot.mean():.2f})")
    print(f"  Under 2.5: {np.mean(tot<=2)*100:.1f}%  Over 2.5: {np.mean(tot>=3)*100:.1f}%  BTTS: {np.mean((gm>=1)&(gk>=1))*100:.1f}%")
    print(f"  Portería a cero MEX: {np.mean(gk==0)*100:.1f}%  | alguna roja: {np.mean(rm|rk)*100:.1f}%")
    print(f"\n  Marcadores mas probables:")
    for (a,b),c in Counter(zip(gm.tolist(),gk.tolist())).most_common(8):
        print(f"      MEX {a}-{b} KOR : {c/n*100:5.2f}%")
    # Probabilidad del resultado REAL
    real=np.mean((gm==1)&(gk==0))
    print(f"\n  >> Probabilidad del marcador REAL (MEX 1-0): {real*100:.2f}%")
    print(f"  Tiempo: {time.time()-t0:.2f}s"); print("#"*70)

if __name__=="__main__": main()
