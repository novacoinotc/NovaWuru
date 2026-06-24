#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCORING DEL BACKTEST — Mundial 2026
Lee backtest.json = {"fixtures":[...con hg/ag...], "predictions":[...con lambda + p...]}
Para cada partido:
  - Calcula P(1/X/2) con Dixon-Coles ANALITICO desde lambda_home/lambda_away (motor uniforme).
  - Compara contra el resultado real.
Metricas: acierto (argmax), Brier multiclase, log-loss, calibracion, MAE de goles,
acierto de marcador exacto, y baselines (siempre local / mayor lambda).
"""
import json, math
import numpy as np

RHO = -0.08
MAXG = 11

def pois(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)

def dc_probs(lh, la, rho=RHO):
    lh=max(lh,1e-3); la=max(la,1e-3)
    M=np.zeros((MAXG,MAXG))
    for x in range(MAXG):
        for y in range(MAXG):
            M[x,y]=pois(x,lh)*pois(y,la)
    # correccion Dixon-Coles
    M[0,0]*=1-lh*la*rho; M[1,0]*=1+la*rho; M[0,1]*=1+lh*rho; M[1,1]*=1-rho
    M/=M.sum()
    ph=np.tril(M,-1).sum()   # x>y local gana
    pd=np.trace(M)
    pa=np.triu(M,1).sum()    # x<y visitante gana
    # marcador modal
    ix=np.unravel_index(np.argmax(M),M.shape)
    return ph,pd,pa,f"{ix[0]}-{ix[1]}"

def outcome(hg,ag): return 'H' if hg>ag else ('A' if ag>hg else 'D')

def main():
    data=json.load(open("backtest.json",encoding='utf-8'))
    fx=data['fixtures']; preds=data['predictions']
    # indexar fixtures por (home,away)
    fmap={}
    for m in fx: fmap[(m['home'].lower(),m['away'].lower())]=m

    rows=[]
    for p in preds:
        key=(p['home'].lower(),p['away'].lower())
        m=fmap.get(key)
        if m is None and 'idx' in p and p['idx']<len(fx): m=fx[p['idx']]
        if m is None: continue
        hg,ag=m['hg'],m['ag']; act=outcome(hg,ag)
        ph,pd,pa,modal=dc_probs(p['lambda_home'],p['lambda_away'])
        # prob del modelo (Dixon-Coles desde lambda) y del agente (directa)
        model={'H':ph,'D':pd,'A':pa}
        s=p['p_home']+p['p_draw']+p['p_away'] or 1
        agentp={'H':p['p_home']/s,'D':p['p_draw']/s,'A':p['p_away']/s}
        rows.append(dict(home=m['home'],away=m['away'],hg=hg,ag=ag,act=act,
                         lh=p['lambda_home'],la=p['lambda_away'],
                         model=model,agentp=agentp,modal=modal,
                         exp_score=p.get('expected_top_score',''),host=m.get('host','')))
    n=len(rows)
    if n==0:
        print("Sin filas para puntuar (revisa backtest.json).");return

    def metrics(probkey,label):
        acc=brier=logloss=0; hits=0
        cal={}  # bucket -> [aciertos, total] sobre la clase predicha
        for r in rows:
            P=r[probkey]; pred=max(P,key=P.get); y=r['act']
            acc+= (pred==y)
            for c in ('H','D','A'):
                brier+=(P[c]-(1 if y==c else 0))**2
            logloss+= -math.log(max(P[y],1e-9))
            b=round(P[pred],1)
            cal.setdefault(b,[0,0]); cal[b][1]+=1; cal[b][0]+=(pred==y)
        print(f"\n  === {label} ===")
        print(f"  Acierto 1X2 (argmax): {acc}/{n} = {acc/n*100:.1f}%")
        print(f"  Brier multiclase (menor=mejor): {brier/n:.4f}")
        print(f"  Log-loss (menor=mejor): {logloss/n:.4f}")
        print(f"  Calibracion (prob predicha -> acierto real):")
        for b in sorted(cal):
            a,t=cal[b]; print(f"    ~{b*100:.0f}%: {a}/{t} aciertos = {a/t*100:.0f}%")
        return acc/n, brier/n, logloss/n

    print("#"*68)
    print(f"#  BACKTEST MUNDIAL 2026 — {n} partidos puntuados")
    print("#"*68)
    macc,_,_=metrics('model',"MODELO (Dixon-Coles desde lambda)")
    aacc,_,_=metrics('agentp',"PROBABILIDAD DIRECTA DEL AGENTE")

    # Baselines
    base_home=sum(1 for r in rows if r['act']=='H')/n
    base_lam=sum(1 for r in rows if (r['lh']>r['la'] and r['act']=='H') or (r['la']>r['lh'] and r['act']=='A') or (abs(r['lh']-r['la'])<1e-6 and r['act']=='D'))/n
    print(f"\n  === BASELINES ===")
    print(f"  Siempre 'gana local/primero': {base_home*100:.1f}%")
    print(f"  Mayor lambda gana: {base_lam*100:.1f}%")

    # Goles
    mae_tot=np.mean([abs((r['lh']+r['la'])-(r['hg']+r['ag'])) for r in rows])
    mae_h=np.mean([abs(r['lh']-r['hg']) for r in rows]); mae_a=np.mean([abs(r['la']-r['ag']) for r in rows])
    avg_pred=np.mean([r['lh']+r['la'] for r in rows]); avg_act=np.mean([r['hg']+r['ag'] for r in rows])
    exact=sum(1 for r in rows if r['exp_score'].replace(' ','')==f"{r['hg']}-{r['ag']}")/n
    modal_exact=sum(1 for r in rows if r['modal']==f"{r['hg']}-{r['ag']}")/n
    print(f"\n  === GOLES Y MARCADOR ===")
    print(f"  Goles totales: predicho prom {avg_pred:.2f} vs real {avg_act:.2f}")
    print(f"  MAE goles totales: {mae_tot:.2f} | MAE local: {mae_h:.2f} | MAE visitante: {mae_a:.2f}")
    print(f"  Acierto marcador exacto (agente): {exact*100:.1f}% | (modal Dixon-Coles): {modal_exact*100:.1f}%")

    # Detalle por partido (predicho vs real)
    print(f"\n  === DETALLE (modelo) ===")
    print(f"  {'PARTIDO':38} {'Pred':>10} {'P(1/X/2)':>18} {'Real':>6} {'OK':>3}")
    for r in sorted(rows,key=lambda z:-max(z['model'].values())):
        P=r['model']; pred=max(P,key=P.get); ok='✓' if pred==r['act'] else '✗'
        nм=f"{r['home'][:17]} vs {r['away'][:16]}"
        print(f"  {nм:38} {r['modal']:>10} {P['H']*100:4.0f}/{P['D']*100:2.0f}/{P['A']*100:2.0f}      {r['hg']}-{r['ag']:<3} {ok:>3}")
    print("#"*68)

if __name__=="__main__":
    main()
