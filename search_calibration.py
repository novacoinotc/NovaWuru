#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BUSQUEDA MASIVA DE CALIBRACION con validacion rigurosa (usa todos los nucleos).
Explora miles de configuraciones de parametros sobre los 28 partidos reales y
selecciona por VALIDACION CRUZADA (no in-sample) para NO sobreajustar.
Ademas hace BOOTSTRAP para saber si la mejora es estadisticamente real o ruido.

Modelo de calibracion (rico):
  lambda_fav' = media*G + dif*S            (G=escala goles, S=ensanche favorito<->debil)
  Dixon-Coles(rho) sobre marcadores bajos
  delta_eff = delta0 + kappa*exp(-|dif|/0.5)   (mas empate cuando el partido es parejo)
  P(empate) *= delta_eff ; renormalizar
"""
import json, math, itertools, time
import numpy as np
from multiprocessing import Pool, cpu_count

MAXG=8

def load_rows():
    data=json.load(open("backtest.json",encoding='utf-8'))
    fmap={(m['home'].lower(),m['away'].lower()):m for m in data['fixtures']}
    rows=[]
    for p in data['predictions']:
        m=fmap.get((p['home'].lower(),p['away'].lower()))
        if not m: continue
        y=0 if m['hg']>m['ag'] else (2 if m['ag']>m['hg'] else 1)
        rows.append((p['lambda_home'],p['lambda_away'],m['hg'],m['ag'],y))
    return rows

# precomputar factoriales
FACT=[math.factorial(k) for k in range(MAXG)]
def pois(k,l): return math.exp(-l)*l**k/FACT[k]

def probs(lh,la,G,S,rho,delta0,kappa):
    m=(lh+la)/2.0; d=(lh-la)/2.0
    lh2=max(m*G+d*S,0.08); la2=max(m*G-d*S,0.08)
    M=np.empty((MAXG,MAXG))
    px=[pois(x,lh2) for x in range(MAXG)]; py=[pois(y,la2) for y in range(MAXG)]
    for x in range(MAXG):
        for y in range(MAXG): M[x,y]=px[x]*py[y]
    M[0,0]*=1-lh2*la2*rho; M[1,0]*=1+la2*rho; M[0,1]*=1+lh2*rho; M[1,1]*=1-rho
    M=np.clip(M,0,None); M/=M.sum()
    ph=np.tril(M,-1).sum(); pd=np.trace(M); pa=np.triu(M,1).sum()
    delta=delta0+kappa*math.exp(-abs(d)/0.5); pd*=delta
    s=ph+pd+pa; return ph/s,pd/s,pa/s

ROWS=load_rows(); N=len(ROWS)

def ll_for_config(cfg):
    G,S,rho,delta0,kappa=cfg
    out=np.empty(N)
    for i,(lh,la,hg,ag,y) in enumerate(ROWS):
        P=probs(lh,la,G,S,rho,delta0,kappa)
        out[i]=-math.log(max(P[y],1e-9))
    return out

def main():
    t0=time.time()
    GRID=dict(G=[0.95,1.0,1.05,1.1,1.15,1.2,1.25],
              S=[1.0,1.1,1.2,1.3,1.4,1.5,1.6,1.8],
              rho=[-0.06,-0.08,-0.10,-0.12,-0.14,-0.18],
              delta0=[1.0,1.05,1.1,1.2,1.3],
              kappa=[0.0,0.1,0.2,0.35])
    configs=list(itertools.product(GRID['G'],GRID['S'],GRID['rho'],GRID['delta0'],GRID['kappa']))
    print("#"*64); print(f"#  BUSQUEDA: {len(configs):,} configuraciones x {N} partidos")
    cores=max(cpu_count()-1,1)
    with Pool(cores) as pool:
        LLrows=pool.map(ll_for_config, configs, chunksize=200)
    LL=np.array(LLrows)                      # [config, partido]
    meanLL=LL.mean(1)
    base_idx=configs.index((1.0,1.0,-0.08,1.0,0.0))
    base=meanLL[base_idx]
    best_in=int(np.argmin(meanLL))
    print(f"#  nucleos {cores} | tiempo busqueda {time.time()-t0:.1f}s"); print("#"*64)
    print(f"\n  BASELINE (sin calibrar): log-loss {base:.4f}")
    print(f"  MEJOR in-sample: {configs[best_in]} -> {meanLL[best_in]:.4f}  (puede ser sobreajuste)")

    # --- Validacion cruzada del PROCEDIMIENTO de seleccion (repeated k-fold) ---
    rng=np.random.default_rng(7)
    K=7; REP=300; proc_loss=0; cnt=0; chosen=np.zeros(len(configs))
    idx=np.arange(N)
    for r in range(REP):
        perm=rng.permutation(idx); folds=np.array_split(perm,K)
        for f in folds:
            test=f; train=np.setdiff1d(idx,test)
            ci=int(np.argmin(LL[:,train].mean(1)))      # elegir config en train
            proc_loss+=LL[ci,test].mean(); cnt+=1; chosen[ci]+=1
    proc_loss/=cnt
    robust=int(np.argmax(chosen))
    print(f"\n  CV del procedimiento (elige-en-train, evalua-en-test, {K}-fold x{REP}):")
    print(f"    Log-loss FUERA DE MUESTRA de 'buscar el mejor': {proc_loss:.4f}")
    print(f"    vs baseline {base:.4f}  -> {'MEJORA REAL' if proc_loss<base else 'NO generaliza (sobreajuste)'}")
    print(f"  Config MAS ELEGIDA en CV (robusta): {configs[robust]} -> in-sample {meanLL[robust]:.4f}")

    # --- Bootstrap: la mejora del config robusto vs baseline es significativa? ---
    diffs=[]
    for b in range(5000):
        s=rng.integers(0,N,N)
        diffs.append(LL[base_idx,s].mean()-LL[robust,s].mean())
    diffs=np.array(diffs); lo,hi=np.percentile(diffs,[2.5,97.5])
    print(f"\n  BOOTSTRAP (5000) mejora log-loss (baseline - robusto):")
    print(f"    media {diffs.mean():+.4f}  IC95% [{lo:+.4f}, {hi:+.4f}]  -> {'SIGNIFICATIVA' if lo>0 else 'NO significativa (cruza 0)'}")

    # Guardar el config robusto si mejora y es razonable
    G,S,rho,delta0,kappa=configs[robust]
    rec=dict(G=G,S=S,rho=rho,delta0=delta0,kappa=kappa,
             cv_logloss=round(proc_loss,4), baseline_logloss=round(base,4),
             bootstrap_mean=round(float(diffs.mean()),4), bootstrap_ci=[round(float(lo),4),round(float(hi),4)],
             note="Config seleccionada por CV del procedimiento; kappa = boost de empate en partidos parejos")
    json.dump(rec,open("search_result.json","w",encoding='utf-8'),ensure_ascii=False,indent=2)
    print(f"\n  -> search_result.json guardado.")
    print("#"*64)

if __name__=="__main__": main()
