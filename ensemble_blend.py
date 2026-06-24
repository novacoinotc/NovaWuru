#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ENSAMBLE: agente-lambda + Elo-lambda. Datos INDEPENDIENTES para reducir varianza.
Deriva lambda desde Elo, prueba modelo Elo-solo, agente-solo y la MEZCLA optima,
seleccionando el peso w por validacion cruzada + bootstrap de significancia.
Requiere elo.json {equipo: elo} y backtest.json.
"""
import json, math
import numpy as np

MAXG=8; FACT=[math.factorial(k) for k in range(MAXG)]
# calibracion base (de calibration.json)
try: CAL=json.load(open("calibration.json",encoding='utf-8'))
except: CAL=dict(G=1.05,S=1.2,rho=-0.12,delta=1.10)
G,S,RHO,DELTA=CAL['G'],CAL['S'],CAL['rho'],CAL.get('delta',CAL.get('delta0',1.1))
HOST_ELO=65.0; TOTAL=2.7

def norm(s): return s.lower().replace('.','').replace('-',' ').strip()
def pois(k,l): return math.exp(-l)*l**k/FACT[k]
def probs(lh,la):
    m=(lh+la)/2; d=(lh-la)/2; lh2=max(m*G+d*S,0.08); la2=max(m*G-d*S,0.08)
    M=np.empty((MAXG,MAXG)); px=[pois(x,lh2) for x in range(MAXG)]; py=[pois(y,la2) for y in range(MAXG)]
    for x in range(MAXG):
        for y in range(MAXG): M[x,y]=px[x]*py[y]
    M[0,0]*=1-lh2*la2*RHO; M[1,0]*=1+la2*RHO; M[0,1]*=1+lh2*RHO; M[1,1]*=1-RHO
    M=np.clip(M,0,None); M/=M.sum()
    ph=np.tril(M,-1).sum(); pd=np.trace(M)*DELTA; pa=np.triu(M,1).sum()
    s=ph+pd+pa; return ph/s,pd/s,pa/s

def main():
    elo={norm(k):v for k,v in json.load(open("elo.json",encoding='utf-8')).items()}
    data=json.load(open("backtest.json",encoding='utf-8'))
    fmap={(m['home'].lower(),m['away'].lower()):m for m in data['fixtures']}
    rows=[]; miss=set()
    for p in data['predictions']:
        m=fmap.get((p['home'].lower(),p['away'].lower()))
        if not m: continue
        eh=elo.get(norm(m['home'])); ea=elo.get(norm(m['away']))
        if eh is None: miss.add(m['home'])
        if ea is None: miss.add(m['away'])
        if eh is None or ea is None: continue
        dr=(eh-(HOST_ELO if m.get('host')==m['home'] else 0))-(ea); dr=eh-ea
        if m.get('host'): dr+=HOST_ELO if m['host']==m['home'] else (-HOST_ELO if m['host']==m['away'] else 0)
        sup=dr/400.0
        le_h=max(TOTAL/2+sup/2,0.15); le_a=max(TOTAL/2-sup/2,0.15)
        y=0 if m['hg']>m['ag'] else (2 if m['ag']>m['hg'] else 1)
        rows.append((p['lambda_home'],p['lambda_away'],le_h,le_a,y))
    if miss: print("  (sin Elo, omitidos):",sorted(miss))
    n=len(rows); print(f"  Partidos con ambas fuentes: {n}")

    def ll_brier(w):
        ll=br=acc=0
        for ah,aa,eh,ea,y in rows:
            lh=w*ah+(1-w)*eh; la=w*aa+(1-w)*ea; P=probs(lh,la)
            ll+=-math.log(max(P[y],1e-9))
            for c in range(3): br+=(P[c]-(1 if y==c else 0))**2
            acc+=(int(np.argmax(P))==y)
        return ll/n,br/n,acc/n

    print(f"\n  {'Fuente':22}{'LogLoss':>9}{'Brier':>8}{'Acierto':>9}")
    for w,lab in [(1.0,'Agentes solo'),(0.0,'Elo solo')]:
        ll,br,ac=ll_brier(w); print(f"  {lab:22}{ll:9.4f}{br:8.4f}{ac*100:8.1f}%")
    # barrido de w + CV
    ws=np.linspace(0,1,21); lls=[ll_brier(w)[0] for w in ws]
    wstar=ws[int(np.argmin(lls))]
    ll,br,ac=ll_brier(wstar); print(f"  {'Mezcla optima w=%.2f'%wstar:22}{ll:9.4f}{br:8.4f}{ac*100:8.1f}%")

    # CV del peso (elige w en train, evalua en test) + bootstrap vs agentes-solo
    rng=np.random.default_rng(11); idx=np.arange(n); K=7; REP=300
    # precomputar ll por (w,partido)
    LLW=np.array([[ -math.log(max(probs(w*ah+(1-w)*eh, w*aa+(1-w)*ea)[y],1e-9))
                    for (ah,aa,eh,ea,y) in rows] for w in ws])
    proc=0;cnt=0;chosen=np.zeros(len(ws))
    for r in range(REP):
        for f in np.array_split(rng.permutation(idx),K):
            tr=np.setdiff1d(idx,f); wi=int(np.argmin(LLW[:,tr].mean(1)))
            proc+=LLW[wi,f].mean(); cnt+=1; chosen[wi]+=1
    proc/=cnt; wrob=ws[int(np.argmax(chosen))]
    agent_ll=LLW[-1].mean()
    print(f"\n  CV del peso (fuera de muestra): log-loss {proc:.4f} | w mas robusto={wrob:.2f}")
    print(f"  Agentes-solo log-loss: {agent_ll:.4f}  -> {'ENSAMBLE MEJORA' if proc<agent_ll else 'no mejora'}")
    diffs=np.array([LLW[-1,s].mean()-LLW[int(np.argmax(chosen)),s].mean() for s in (rng.integers(0,n,n) for _ in range(5000))])
    lo,hi=np.percentile(diffs,[2.5,97.5])
    print(f"  Bootstrap mejora (agentes - ensamble): media {diffs.mean():+.4f} IC95% [{lo:+.4f},{hi:+.4f}] -> {'SIGNIFICATIVA' if lo>0 else 'NO significativa'}")
    json.dump(dict(w_robust=float(wrob),cv_logloss=round(proc,4),agent_logloss=round(float(agent_ll),4)),
              open("ensemble_result.json","w"),indent=2)

if __name__=="__main__": main()
