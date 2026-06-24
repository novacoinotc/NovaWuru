#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PREDICTOR CALIBRADO reutilizable — el "oro" para proximos partidos.
Toma los goles esperados (lambda) de cualquier fuente (agente, motor de gemelos,
o Elo) y aplica la calibracion aprendida de datos reales (calibration.json) +
Dixon-Coles para devolver probabilidades 1X2, marcadores y cuotas justas.

USO:  python3 predict_match.py <lambda_local> <lambda_visit> [Local] [Visit]
EJEMPLO (Mexico vs Corea):  python3 predict_match.py 1.34 0.92 Mexico Corea
"""
import json, math, sys
import numpy as np

def load_cal():
    try: return json.load(open("calibration.json",encoding='utf-8'))
    except FileNotFoundError: return dict(G=1.0,S=1.0,rho=-0.10,delta=1.0)

def pois(k,l): return math.exp(-l)*l**k/math.factorial(k)

def predict(lh, la, cal=None):
    cal=cal or load_cal(); G,S,rho,delta=cal['G'],cal['S'],cal['rho'],cal['delta']
    m=(lh+la)/2.0; d=(lh-la)/2.0
    lh2=max(m*G+d*S,0.08); la2=max(m*G-d*S,0.08)
    M=np.zeros((11,11))
    for x in range(11):
        for y in range(11): M[x,y]=pois(x,lh2)*pois(y,la2)
    M[0,0]*=1-lh2*la2*rho; M[1,0]*=1+la2*rho; M[0,1]*=1+lh2*rho; M[1,1]*=1-rho
    M=np.clip(M,0,None); M/=M.sum()
    ph=float(np.tril(M,-1).sum()); pd=float(np.trace(M)); pa=float(np.triu(M,1).sum())
    pd*=delta; s=ph+pd+pa; ph/=s; pd/=s; pa/=s
    scores=[((x,y),float(M[x,y])) for x in range(6) for y in range(6)]
    scores.sort(key=lambda z:-z[1])
    tot=float((M*np.add.outer(range(11),range(11))).sum())
    o25=float(sum(M[x,y] for x in range(11) for y in range(11) if x+y>=3))
    btts=float(sum(M[x,y] for x in range(1,11) for y in range(1,11)))
    return dict(lh_adj=lh2,la_adj=la2,p_home=ph,p_draw=pd,p_away=pa,
                exp_total=tot,over25=o25,btts=btts,top=scores[:6])

def fair(p): return round(1/p,2) if p>0 else 99.9

if __name__=="__main__":
    if len(sys.argv)<3:
        print("USO: python3 predict_match.py <lambda_local> <lambda_visit> [Local] [Visit]"); sys.exit(1)
    lh=float(sys.argv[1]); la=float(sys.argv[2])
    H=sys.argv[3] if len(sys.argv)>3 else "Local"; A=sys.argv[4] if len(sys.argv)>4 else "Visit"
    cal=load_cal(); r=predict(lh,la,cal)
    print(f"\n  Calibracion: G={cal['G']} S={cal['S']} rho={cal['rho']} delta={cal['delta']}")
    print(f"  lambda entrada: {H} {lh} - {la} {A}   -> ajustado: {r['lh_adj']:.2f} - {r['la_adj']:.2f}")
    print(f"  {'-'*48}")
    print(f"  Gana {H:8}: {r['p_home']*100:5.1f}%  (cuota justa {fair(r['p_home'])})")
    print(f"  Empate    : {r['p_draw']*100:5.1f}%  (cuota justa {fair(r['p_draw'])})")
    print(f"  Gana {A:8}: {r['p_away']*100:5.1f}%  (cuota justa {fair(r['p_away'])})")
    print(f"  Goles esperados (total): {r['exp_total']:.2f}  | Over2.5 {r['over25']*100:.0f}%  | BTTS {r['btts']*100:.0f}%")
    print(f"  Marcadores mas probables:")
    for (x,y),p in r['top']: print(f"     {H} {x}-{y} {A}: {p*100:4.1f}%")
