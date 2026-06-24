#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CALIBRACION del modelo con DATOS REALES (28 partidos del Mundial 2026).
Ajusta 4 parametros globales que corrigen los sesgos detectados en el backtest:
  G     = escala de goles (corrige subestimacion total)
  S     = ensanche favorito<->debil (corrige timidez de lambda en equipos fuertes)
  rho   = correccion Dixon-Coles de marcadores bajos (empates 0-0,1-0,0-1,1-1)
  delta = multiplicador del empate (corrige exceso de empates observado)

Selecciona por LEAVE-ONE-OUT CROSS-VALIDATION (log-loss fuera de muestra) para
NO sobreajustar a la muestra. Guarda calibration.json.
"""
import json, math
import numpy as np

def pois(k,l): return math.exp(-l)*l**k/math.factorial(k)

def probs(lh, la, G, S, rho, delta):
    m=(lh+la)/2.0; d=(lh-la)/2.0
    lh2=max(m*G+d*S, 0.08); la2=max(m*G-d*S, 0.08)
    M=np.zeros((11,11))
    for x in range(11):
        px=pois(x,lh2)
        for y in range(11):
            M[x,y]=px*pois(y,la2)
    M[0,0]*=1-lh2*la2*rho; M[1,0]*=1+la2*rho; M[0,1]*=1+lh2*rho; M[1,1]*=1-rho
    M=np.clip(M,0,None); M/=M.sum()
    ph=np.tril(M,-1).sum(); pd=np.trace(M); pa=np.triu(M,1).sum()
    pd*=delta; s=ph+pd+pa; ph/=s; pd/=s; pa/=s            # boost de empate + renormalizar
    ix=np.unravel_index(np.argmax(M),M.shape)
    return ph,pd,pa,(lh2+la2),f"{ix[0]}-{ix[1]}"

def outc(h,a): return 0 if h>a else (2 if a>h else 1)   # 0=H,1=D,2=A

def load():
    data=json.load(open("backtest.json",encoding='utf-8'))
    fmap={(m['home'].lower(),m['away'].lower()):m for m in data['fixtures']}
    rows=[]
    for p in data['predictions']:
        m=fmap.get((p['home'].lower(),p['away'].lower()))
        if not m: continue
        rows.append((p['lambda_home'],p['lambda_away'],m['hg'],m['ag'],outc(m['hg'],m['ag'])))
    return rows

def metrics_for(rows, G,S,rho,delta):
    ll=br=acc=mae=0
    for lh,la,hg,ag,y in rows:
        ph,pd,pa,tot,_=probs(lh,la,G,S,rho,delta); P=[ph,pd,pa]
        ll+=-math.log(max(P[y],1e-9))
        for c in range(3): br+=(P[c]-(1 if y==c else 0))**2
        acc+=(int(np.argmax(P))==y); mae+=abs(tot-(hg+ag))
    n=len(rows); return ll/n, br/n, acc/n, mae/n

def main():
    rows=load(); n=len(rows)
    GRID_G=[0.95,1.0,1.05,1.10,1.20]
    GRID_S=[1.0,1.15,1.30,1.50,1.70]
    GRID_R=[-0.06,-0.10,-0.14,-0.18]
    GRID_D=[1.0,1.15,1.30,1.45]
    combos=[(G,S,r,d) for G in GRID_G for S in GRID_S for r in GRID_R for d in GRID_D]

    # Matriz log-loss por (combo, partido)
    LL=np.zeros((len(combos), n))
    for ci,(G,S,r,d) in enumerate(combos):
        for ri,(lh,la,hg,ag,y) in enumerate(rows):
            P=probs(lh,la,G,S,r,d)[:3]
            LL[ci,ri]=-math.log(max(P[y],1e-9))

    # In-sample: combo con menor log-loss medio
    mean_ll=LL.mean(1); best_in=int(np.argmin(mean_ll))

    # Leave-one-out: para cada partido, elige combo optimo SIN ese partido y evalua en el
    loo=0; chosen=np.zeros(len(combos))
    for i in range(n):
        mask=np.ones(n,bool); mask[i]=False
        ci=int(np.argmin(LL[:,mask].mean(1)))
        loo+=LL[ci,i]; chosen[ci]+=1
    loo/=n
    best_loo=int(np.argmax(chosen))   # combo mas elegido en CV (robusto)

    print("#"*64); print(f"#  CALIBRACION con datos reales ({n} partidos)"); print("#"*64)
    base=metrics_for(rows,1.0,1.0,-0.08,1.0)
    print(f"\n  BASELINE (sin calibrar G1 S1 rho-.08 d1):")
    print(f"    LogLoss {base[0]:.4f} | Brier {base[1]:.4f} | Acierto {base[2]*100:.1f}% | MAEgoles {base[3]:.2f}")

    for tag,ci in [("MEJOR in-sample",best_in),("MAS ROBUSTO (LOO-CV)",best_loo)]:
        G,S,r,d=combos[ci]; mm=metrics_for(rows,G,S,r,d)
        print(f"\n  {tag}: G={G} S={S} rho={r} delta={d}")
        print(f"    LogLoss {mm[0]:.4f} | Brier {mm[1]:.4f} | Acierto {mm[2]*100:.1f}% | MAEgoles {mm[3]:.2f}")
    print(f"\n  Log-loss LEAVE-ONE-OUT (fuera de muestra): {loo:.4f}  (baseline {base[0]:.4f})")

    # Parametros finales = el mas robusto en CV
    G,S,r,d=combos[best_loo]
    cal=dict(G=G,S=S,rho=r,delta=d,
             fitted_on="28 partidos Mundial 2026 (J1+J2 parcial)",
             baseline_logloss=round(base[0],4), calibrated_logloss=round(metrics_for(rows,G,S,r,d)[0],4),
             loo_logloss=round(loo,4))
    json.dump(cal,open("calibration.json","w",encoding='utf-8'),ensure_ascii=False,indent=2)
    print(f"\n  -> Guardado calibration.json: {cal}")
    print("#"*64)

if __name__=="__main__": main()
