#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Motor genérico: simula UN partido con gemelos de jugadores (home/away) + entorno.
Lee un JSON de partido {meta, env, home:{team,players[11]}, away:{team,players[11]}}.
Reusa la logica del motor v2 (creacion vs conversion, portero, aereo, pace, fatiga)
y aplica la calibracion. Corre 100k Monte Carlo. Uso: python3 sim_match.py match_X.json
"""
import json, sys, math
import numpy as np
from collections import Counter
from multiprocessing import Pool, cpu_count

N=100000; MINUTES=96
CAL=json.load(open("calibration.json",encoding='utf-8'))
G,S=CAL['G'],CAL['S']; RHO=CAL['rho']; DELTA=CAL.get('delta',1.1)
# Base de fuerza por Elo calibrado (provee el DIFERENCIAL de nivel; los gemelos modulan alrededor)
CALE=json.load(open("calibration_elo.json",encoding='utf-8'))
TOTAL,GP400,HOSTELO=CALE['TOTAL'],CALE['GP400'],CALE['HOST']
ELO={k.lower():v for k,v in json.load(open("elo.json",encoding='utf-8')).items()}
ELO['usa']=ELO.get('united states',1780); ELO['turkiye']=ELO.get('turkiye',ELO.get('turkey',1849))
def team_elo(name):
    n=name.lower()
    return ELO.get(n, ELO.get(n.replace('.','').strip(), 1600))
def elo_base_lams(home,away,host_home,host_away):
    dr=(team_elo(home)-team_elo(away))+(HOSTELO if host_home else 0)-(HOSTELO if host_away else 0)
    sup=dr/400.0*GP400
    return max(TOTAL/2+sup/2,0.25), max(TOTAL/2-sup/2,0.25)

def rw(pos):
    p=pos.lower()
    if 'portero' in p or 'gk' in p or 'arquero' in p: return (0.0,1.0,0.0)
    if 'central' in p or 'zaguero' in p or 'cb' in p: return (0.05,1.0,0.05)
    if 'lateral' in p or 'defensa' in p or 'back' in p or 'rb' in p or 'lb' in p: return (0.25,0.85,0.15)
    if 'contenc' in p or 'pivote' in p or 'defensivo' in p or 'cdm' in p or 'volante de marca' in p: return (0.30,0.70,0.30)
    if 'mediapunta' in p or 'ofensiv' in p or 'enganche' in p or '10' in p or 'cam' in p: return (0.85,0.20,0.95)
    if 'extremo' in p or 'winger' in p or 'banda' in p or 'lw' in p or 'rw' in p: return (0.90,0.20,0.70)
    if 'delantero' in p or 'punta' in p or 'centro' in p or 'striker' in p or 'st' in p or '9' in p: return (1.0,0.10,0.55)
    if 'medio' in p or 'mid' in p or 'interior' in p or 'cm' in p: return (0.60,0.45,0.85)
    return (0.5,0.5,0.5)

def arr(players):
    f=lambda k,d=50:np.array([float(p.get(k,d)) for p in players])
    A=dict(skill=f('skill'),finishing=f('finishing'),creativity=f('creativity'),pace=f('pace',60),
           aerial=f('aerial'),defense=f('defense'),stamina=f('stamina_base'),comp=f('composure_mean'),
           vol=f('composure_volatility',12),clutch=f('clutch'),disc=f('discipline'),cons=f('consistency'),
           mot=f('motivation_today'),inj=f('injury_risk',20),height=f('height_cm',180),
           tspeed=f('top_speed_kmh',31),dur=f('durability',70))
    wa,wd,wc=zip(*[rw(p['position']) for p in players])
    A['wa']=np.array(wa);A['wd']=np.array(wd);A['wc']=np.array(wc)
    return A

def create(A,form,mind,mot):
    off=(0.5*A['finishing'][:,None]+0.3*A['creativity'][:,None]+0.2*A['skill'][:,None])*form*mind*mot
    return 0.7*(A['wa'][:,None]*off).sum(0)+0.3*(A['wc'][:,None]*off).sum(0)
def defend(A,form,mind):
    d=(0.6*A['defense'][:,None]+0.2*A['aerial'][:,None]+0.2*A['skill'][:,None])*form*mind
    return (A['wd'][:,None]*d).sum(0)
def base_idx(A):
    o=np.ones((len(A['skill']),1));return float(create(A,o,o,o)[0]),float(defend(A,o,o)[0])
def gk(A):
    # portero = jugador con wd alto y wa 0
    idx=[i for i,(a,d,c) in enumerate(zip(A['wa'],A['wd'],A['wc'])) if a==0.0 and d==1.0]
    if not idx: idx=[int(np.argmax(A['wd']))]
    i=idx[0]; return 0.7*A['skill'][i]+0.3*A['comp'][i], A['vol'][i]+8

def aerial_idx(A):
    w=A['wd']+A['wa']; return float(np.average(0.6*(A['height']-170)+0.4*(A['aerial']-50),weights=np.clip(w,0.05,None)))
def pace_idx(A):
    w=A['wa']; return float(np.average(0.5*A['pace']+0.5*(A['tspeed']-28)*8,weights=np.clip(w,0.05,None)))

def worker(args):
    AH,AA,env,host_home,host_away,n,seed,baseH,baseA,eloLamH,eloLamA=args
    rng=np.random.default_rng(seed)
    def day(A):
        P=len(A['skill']);cons=A['cons'][:,None]
        form=1+rng.standard_normal((P,n))*(1-cons/100)*0.30
        comp=np.clip(rng.normal(A['comp'][:,None]+(A['clutch'][:,None]-50)*0.10,A['vol'][:,None]),10,100)
        mind=comp/np.clip(A['comp'][:,None],20,100)
        mot=np.clip(A['mot'][:,None]+rng.normal(0,5,(P,n)),0,100)/np.clip(A['mot'].mean(),40,100)
        frail=np.maximum(A['inj'][:,None],100-A['dur'][:,None])
        form=np.where(rng.random((P,n))<frail/100*0.05,form*0.5,form)
        return form,mind,mot
    fH,mH,moH=day(AH); fA,mA,moA=day(AA)
    cH=create(AH,fH,mH,moH)/baseH[0]; cA=create(AA,fA,mA,moA)/baseA[0]
    dH=baseH[1]/defend(AH,fH,mH); dA=baseA[1]/defend(AA,fA,mA)
    finH=np.clip(((AH['finishing'][:,None]*fH).mean(0))/75,0.85,1.2)
    finA=np.clip(((AA['finishing'][:,None]*fA).mean(0))/75,0.85,1.2)
    skH,vH=gk(AH); skA,vA=gk(AA)
    gkfacH=np.clip(1+(72-rng.normal(skA,vA,n))/90,0.75,1.30)  # gol H sube si GK A falla
    gkfacA=np.clip(1+(72-rng.normal(skH,vH,n))/90,0.75,1.30)
    spH=0.05*max(aerial_idx(AH)-aerial_idx(AA),-8)/6.0; spA=0.05*max(aerial_idx(AA)-aerial_idx(AH),-8)/6.0
    rain=rng.random(n)<env.get('rain_probability_kickoff',0.2); wet=1+0.5*rain
    pcH=pace_idx(AH);pcA=pace_idx(AA)
    cntH=1+0.0013*(pcH-pcA)*wet; cntA=1+0.0013*(pcA-pcH)*wet
    crowd=np.clip(rng.normal(env.get('crowd_noise',70),8,n),0,100)
    crowd_boost=1+0.0012*(crowd-50)   # aficion (la ventaja de anfitrion ya esta en la base Elo)
    lamH=eloLamH*cH*dA*finH*gkfacH*crowd_boost+spH
    lamA=eloLamA*cA*dH*finA*gkfacA*(np.where(rain,1.04,1.0))*cntA+spA
    lamH=np.clip(lamH*np.where(rain,0.98,1.0)*cntH,0.12,5); lamA=np.clip(lamA,0.12,5)
    stH=(AH['stamina'].mean()-50)*0.4+8; stA=(AA['stamina'].mean()-50)*0.4+8
    cardH=100-AH['disc'].mean(); cardA=100-AA['disc'].mean()
    gm=np.zeros(n,np.int16);ga=np.zeros(n,np.int16);rm=np.zeros(n,bool);ra=np.zeros(n,bool)
    r0h=lamH/90;r0a=lamA/90
    for t in range(1,MINUTES+1):
        if t>60:
            ph=(t-60)/36;fmh=1+(stH/100)*ph*0.8+0.10*ph;fma=1+(stA/100)*ph*0.8+0.10*ph
        else: fmh=fma=1.0
        diff=gm-ga
        ph_=np.where(diff<0,1.18,np.where(diff>0,0.92,1.0));pa_=np.where(diff>0,1.18,np.where(diff<0,0.92,1.0))
        rch=np.where(rm,0.72,1.0)*np.where(ra,1.15,1.0);rca=np.where(ra,0.72,1.0)*np.where(rm,1.15,1.0)
        gm+=(rng.random(n)<r0h*fmh*ph_*rch).astype(np.int16);ga+=(rng.random(n)<r0a*fma*pa_*rca).astype(np.int16)
        rm|=(rng.random(n)<(cardH/100)*0.0009*(1+0.5*(diff<0)))&(~rm)
        ra|=(rng.random(n)<(cardA/100)*0.0009*(1+0.5*(diff>0)))&(~ra)
    return gm,ga,lamH.mean(),lamA.mean()

def run(M):
    home=M['home'];away=M['away'];env=M.get('env') or {}
    AH=arr(home['players']);AA=arr(away['players'])
    bh=base_idx(AH);ba=base_idx(AA)
    meta=M['meta'];host_home=meta.get('host')==meta.get('home');host_away=meta.get('host')==meta.get('away')
    eloLamH,eloLamA=elo_base_lams(meta['home'],meta['away'],host_home,host_away)
    cores=max(cpu_count()-1,1);chunk=N//cores
    with Pool(cores) as pool:
        res=pool.map(worker,[(AH,AA,env,host_home,host_away,chunk,7+i,bh,ba,eloLamH,eloLamA) for i in range(cores)])
    gm=np.concatenate([r[0] for r in res]);ga=np.concatenate([r[1] for r in res])
    lh=np.mean([r[2] for r in res]);la=np.mean([r[3] for r in res])
    n=len(gm);hw,dr,aw=np.mean(gm>ga),np.mean(gm==ga),np.mean(gm<ga)
    H=meta['home'];A=meta['away']
    print(f"\n  {'='*60}\n  {H} vs {A}  (Grupo {meta['group']}, {meta['venue']})")
    print(f"  lambda: {H} {lh:.2f} - {la:.2f} {A}")
    print(f"  Gana {H}: {hw*100:.1f}%  |  Empate: {dr*100:.1f}%  |  Gana {A}: {aw*100:.1f}%")
    tot=gm+ga
    print(f"  Goles esp: {gm.mean():.2f}-{ga.mean():.2f} (tot {tot.mean():.2f}) | Over2.5 {np.mean(tot>=3)*100:.0f}% | BTTS {np.mean((gm>=1)&(ga>=1))*100:.0f}%")
    top=Counter(zip(gm.tolist(),ga.tolist())).most_common(4)
    print("  Marcadores: "+" · ".join(f"{a}-{b} {c/n*100:.0f}%" for (a,b),c in top))
    return dict(home=H,away=A,pH=hw,pD=dr,pA=aw,top=top[0])

if __name__=="__main__":
    M=json.load(open(sys.argv[1],encoding='utf-8')); run(M)
