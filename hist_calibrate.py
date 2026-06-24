#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CALIBRACION HISTORICA del motor Elo->Dixon-Coles sobre 124 partidos de fase de
grupos (Mundiales 2018 + 2022 + 2026). Muestra grande => poder estadistico real.
Ajusta parametros GENERALES y transferibles:
  TOTAL  = goles totales base por partido
  GP400  = goles de supremacia por cada 400 de Elo (pendiente Elo->goles)
  HOST   = ventaja del anfitrion en puntos Elo
  rho    = correccion Dixon-Coles de marcadores bajos
  delta  = multiplicador de empate
Selecciona por CV del procedimiento + BOOTSTRAP de significancia.
"""
import json, math, itertools, time
import numpy as np
from multiprocessing import Pool, cpu_count

MAXG=9; FACT=[math.factorial(k) for k in range(MAXG)]
def pois(k,l): return math.exp(-l)*l**k/FACT[k]
def norm(s): return s.lower().replace('.','').replace('-',' ').strip()

def build_rows():
    rows=[]
    for mf,ef in [("hist2018.json","elo2018.json"),("hist2022.json","elo2022.json"),("backtest.json","elo.json")]:
        elo={norm(k):v for k,v in json.load(open(ef,encoding='utf-8')).items()}
        raw=json.load(open(mf,encoding='utf-8'))
        matches = raw if isinstance(raw,list) else raw['fixtures']
        for m in matches:
            eh=elo.get(norm(m['home'])); ea=elo.get(norm(m['away']))
            if eh is None or ea is None: continue
            hostadj=0
            if m.get('host'):
                if norm(m['host'])==norm(m['home']): hostadj=1
                elif norm(m['host'])==norm(m['away']): hostadj=-1
            y=0 if m['hg']>m['ag'] else (2 if m['ag']>m['hg'] else 1)
            rows.append((eh,ea,hostadj,m['hg'],m['ag'],y))
    return rows

ROWS=build_rows(); N=len(ROWS)

def probs(eh,ea,hostadj,TOTAL,GP400,HOST,rho,delta):
    dr=(eh-ea)+hostadj*HOST
    sup=dr/400.0*GP400
    lh=max(TOTAL/2+sup/2,0.08); la=max(TOTAL/2-sup/2,0.08)
    M=np.empty((MAXG,MAXG)); px=[pois(x,lh) for x in range(MAXG)]; py=[pois(y,la) for y in range(MAXG)]
    for x in range(MAXG):
        for y in range(MAXG): M[x,y]=px[x]*py[y]
    M[0,0]*=1-lh*la*rho; M[1,0]*=1+la*rho; M[0,1]*=1+lh*rho; M[1,1]*=1-rho
    M=np.clip(M,0,None); M/=M.sum()
    ph=np.tril(M,-1).sum(); pd=np.trace(M)*delta; pa=np.triu(M,1).sum()
    s=ph+pd+pa; return ph/s,pd/s,pa/s

def ll_for(cfg):
    TOTAL,GP400,HOST,rho,delta=cfg; out=np.empty(N)
    for i,(eh,ea,h,hg,ag,y) in enumerate(ROWS):
        P=probs(eh,ea,h,TOTAL,GP400,HOST,rho,delta); out[i]=-math.log(max(P[y],1e-9))
    return out

def metrics(cfg):
    TOTAL,GP400,HOST,rho,delta=cfg; ll=br=acc=mae=0
    for eh,ea,h,hg,ag,y in ROWS:
        P=probs(eh,ea,h,TOTAL,GP400,HOST,rho,delta)
        ll+=-math.log(max(P[y],1e-9))
        for c in range(3): br+=(P[c]-(1 if y==c else 0))**2
        acc+=(int(np.argmax(P))==y)
    return ll/N,br/N,acc/N

def main():
    t0=time.time()
    print("#"*64); print(f"#  CALIBRACION HISTORICA — {N} partidos (2018+2022+2026)")
    GRID=dict(TOTAL=[2.4,2.5,2.6,2.7,2.8,2.9,3.0],GP400=[0.7,0.85,1.0,1.15,1.3,1.5],
              HOST=[0,40,70,100,130],rho=[-0.04,-0.08,-0.12,-0.16],delta=[1.0,1.08,1.16])
    configs=list(itertools.product(*GRID.values()))
    cores=max(cpu_count()-1,1)
    with Pool(cores) as pool: LL=np.array(pool.map(ll_for,configs,chunksize=100))
    meanLL=LL.mean(1)
    base=(2.7,1.0,0,-0.08,1.0); bi=configs.index(base)
    besti=int(np.argmin(meanLL))
    print(f"#  {len(configs):,} configs x {N} | {cores} nucleos | {time.time()-t0:.1f}s"); print("#"*64)
    bm=metrics(base); print(f"\n  BASELINE {base}: LogLoss {bm[0]:.4f} Brier {bm[1]:.4f} Acierto {bm[2]*100:.1f}%")
    em=metrics(configs[besti]); print(f"  MEJOR in-sample {configs[besti]}: LogLoss {em[0]:.4f} Brier {em[1]:.4f} Acierto {em[2]*100:.1f}%")

    rng=np.random.default_rng(3); idx=np.arange(N); K=8; REP=200
    proc=0;cnt=0;chosen=np.zeros(len(configs))
    for r in range(REP):
        for f in np.array_split(rng.permutation(idx),K):
            tr=np.setdiff1d(idx,f); ci=int(np.argmin(LL[:,tr].mean(1)))
            proc+=LL[ci,f].mean();cnt+=1;chosen[ci]+=1
    proc/=cnt; rob=int(np.argmax(chosen))
    print(f"\n  CV del procedimiento ({K}-fold x{REP}): LogLoss fuera de muestra {proc:.4f}  vs baseline {bm[0]:.4f}")
    print(f"  -> {'MEJORA REAL' if proc<bm[0] else 'no mejora'}")
    print(f"  Config robusta (mas elegida en CV): {configs[rob]}")
    rmet=metrics(configs[rob]); print(f"     -> LogLoss {rmet[0]:.4f} Brier {rmet[1]:.4f} Acierto {rmet[2]*100:.1f}%")
    diffs=np.array([LL[bi,s].mean()-LL[rob,s].mean() for s in (rng.integers(0,N,N) for _ in range(8000))])
    lo,hi=np.percentile(diffs,[2.5,97.5])
    print(f"\n  BOOTSTRAP (8000) mejora (baseline - robusto): media {diffs.mean():+.4f} IC95% [{lo:+.4f},{hi:+.4f}] -> {'SIGNIFICATIVA ✓' if lo>0 else 'NO significativa'}")

    T,G,H,r,d=configs[rob]
    cal=dict(TOTAL=T,GP400=G,HOST=H,rho=r,delta=d,n_matches=N,
             baseline_logloss=round(bm[0],4),calibrated_logloss=round(rmet[0],4),cv_logloss=round(proc,4),
             bootstrap_mean=round(float(diffs.mean()),4),bootstrap_ci=[round(float(lo),4),round(float(hi),4)],
             note="Motor Elo->Dixon-Coles calibrado sobre 124 partidos de Mundiales (2018+2022+2026). Parametros generales transferibles.")
    json.dump(cal,open("calibration_elo.json","w",encoding='utf-8'),ensure_ascii=False,indent=2)
    print(f"\n  -> calibration_elo.json guardado: TOTAL={T} GP400={G} HOST={H} rho={r} delta={d}")
    print("#"*64)

if __name__=="__main__": main()
