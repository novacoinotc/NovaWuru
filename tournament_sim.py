#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SIMULADOR MONTE CARLO DEL TORNEO COMPLETO — Mundial 2026
Modelo: Elo calibrado (calibration_elo.json) -> Dixon-Coles. Simula los partidos
de grupo pendientes + toda la llave (R32->Final) N veces y agrega probabilidades
de avance (16avos, 8vos, 4tos, semis, final, campeon) y proyecta el bracket.
Usa todos los nucleos (multiprocessing).
"""
import json, math, random
import numpy as np
from collections import defaultdict
from multiprocessing import Pool, cpu_count

N_SIMS=50000
ST=json.load(open("tournament_state.json",encoding='utf-8'))
ELO_RAW=json.load(open("elo.json",encoding='utf-8'))
CAL=json.load(open("calibration_elo.json",encoding='utf-8'))
TOTAL,GP400,HOST,RHO=CAL['TOTAL'],CAL['GP400'],CAL['HOST'],CAL['rho']
HOSTS={"Mexico","Canada","USA"}

def norm(s): return s.lower().replace('.','').replace('-',' ').strip()
ELO={norm(k):v for k,v in ELO_RAW.items()}
ELO['usa']=ELO.get('united states',ELO.get('usa',1780))
def elo(t): return ELO.get(norm(t),1600)

GROUPS=ST['groups']; FIX=ST['fixtures']
# slots de mejores terceros y sus grupos permitidos (estructura oficial R32)
THIRD_SLOTS={'M74':set('ABCDF'),'M77':set('CDFGH'),'M79':set('CEFHI'),'M80':set('EHIJK'),
             'M81':set('BEFIJ'),'M82':set('AEHIJ'),'M85':set('EFGIJ'),'M87':set('DEIJL')}

def lam(eh,ea,host_h=0,host_a=0):
    dr=(eh-ea)+(HOST if host_h else 0)-(HOST if host_a else 0)
    sup=dr/400.0*GP400
    return max(TOTAL/2+sup/2,0.08), max(TOTAL/2-sup/2,0.08)

def sim_goals(rng,th,ta,host=False):
    hh = host and th in HOSTS; ha = host and ta in HOSTS
    lh,la=lam(elo(th),elo(ta),hh,ha)
    return rng.poisson(lh), rng.poisson(la)

def ko_winner(rng,th,ta):
    gh,ga=sim_goals(rng,th,ta,host=False)
    if gh>ga: return th
    if ga>gh: return ta
    # prorroga/penales por expectativa Elo
    p=1/(1+10**(-(elo(th)-elo(ta))/400))
    return th if rng.random()<p else ta

def bipartite(thirds):
    # thirds: list of (team, groupletter). asigna a slots respetando grupos permitidos.
    slots=list(THIRD_SLOTS); adj={s:[i for i,(t,g) in enumerate(thirds) if g in THIRD_SLOTS[s]] for s in slots}
    matchT={}  # third_idx -> slot
    def try_k(s,seen):
        for i in adj[s]:
            if i in seen: continue
            seen.add(i)
            if i not in matchT or try_k(matchT[i],seen):
                matchT[i]=s; return True
        return False
    order=sorted(slots,key=lambda s:len(adj[s]))
    for s in order: try_k(s,set())
    res={matchT[i]:thirds[i][0] for i in matchT}
    # rellenar slots faltantes con terceros sin asignar (fallback)
    used=set(res.values()); rem=[t for t,g in thirds if t not in used]
    for s in slots:
        if s not in res and rem: res[s]=rem.pop()
    return res

def run_chunk(args):
    nsim,seed=args; rng=np.random.default_rng(seed)
    cnt=defaultdict(lambda: defaultdict(int))
    for _ in range(nsim):
        # --- grupos ---
        tab={t:[0,0,0] for g in GROUPS.values() for t in g}  # pts,gd,gf
        for f in FIX:
            h,a=f['home'],f['away']
            if f['hg'] is not None: gh,ga=f['hg'],f['ag']
            else: gh,ga=sim_goals(rng,h,a,host=True)
            tab[h][2]+=gh; tab[a][2]+=ga; tab[h][1]+=gh-ga; tab[a][1]+=ga-gh
            if gh>ga: tab[h][0]+=3
            elif ga>gh: tab[a][0]+=3
            else: tab[h][0]+=1; tab[a][0]+=1
        pos={}; thirds=[]
        for gl,teams in GROUPS.items():
            rank=sorted(teams,key=lambda t:(tab[t][0],tab[t][1],tab[t][2],rng.random()),reverse=True)
            pos[('1',gl)]=rank[0]; pos[('2',gl)]=rank[1]; thirds.append((rank[2],gl))
            for t in rank[:2]:
                cnt[t]['qual']+=1
            cnt[rank[0]]['win']+=1; cnt[rank[1]]['2nd']+=1
        # mejores 8 terceros
        thirds_sorted=sorted(thirds,key=lambda x:(tab[x[0]][0],tab[x[0]][1],tab[x[0]][2],rng.random()),reverse=True)
        top8=thirds_sorted[:8]
        for t,g in top8: cnt[t]['qual']+=1
        slotT=bipartite(top8)
        def P(pp): return pos[pp]
        T=lambda s: slotT.get(s, top8[0][0])
        # --- R32 (matches 73-88) ---
        r32={73:(P(('2','A')),P(('2','B'))),74:(P(('1','E')),T('M74')),75:(P(('1','F')),P(('2','C'))),
             76:(P(('1','C')),P(('2','F'))),77:(P(('1','I')),T('M77')),78:(P(('2','E')),P(('2','I'))),
             79:(P(('1','A')),T('M79')),80:(P(('1','L')),T('M80')),81:(P(('1','D')),T('M81')),
             82:(P(('1','G')),T('M82')),83:(P(('2','K')),P(('2','L'))),84:(P(('1','H')),P(('2','J'))),
             85:(P(('1','B')),T('M85')),86:(P(('1','J')),P(('2','H'))),87:(P(('1','K')),T('M87')),
             88:(P(('2','D')),P(('2','G')))}
        w={}
        for m,(x,y) in r32.items():
            for t in (x,y): cnt[t]['r32']+=1
            w[m]=ko_winner(rng,x,y); cnt[w[m]]['r16']+=1
        # R16 (89-96)
        r16={89:(w[73],w[75]),90:(w[74],w[77]),91:(w[76],w[78]),92:(w[79],w[80]),
             93:(w[83],w[84]),94:(w[81],w[82]),95:(w[86],w[88]),96:(w[85],w[87])}
        for m,(x,y) in r16.items(): w[m]=ko_winner(rng,x,y); cnt[w[m]]['qf']+=1
        # QF (97-100)
        qf={97:(w[89],w[90]),98:(w[93],w[94]),99:(w[91],w[92]),100:(w[95],w[96])}
        for m,(x,y) in qf.items(): w[m]=ko_winner(rng,x,y); cnt[w[m]]['sf']+=1
        # SF (101-102)
        sf={101:(w[97],w[98]),102:(w[99],w[100])}
        for m,(x,y) in sf.items(): w[m]=ko_winner(rng,x,y); cnt[w[m]]['fin']+=1
        champ=ko_winner(rng,w[101],w[102]); cnt[champ]['champ']+=1
    return {t:dict(d) for t,d in cnt.items()}

def main():
    cores=max(cpu_count()-1,1); per=N_SIMS//cores
    with Pool(cores) as pool:
        parts=pool.map(run_chunk,[(per,1000+i) for i in range(cores)])
    tot=defaultdict(lambda: defaultdict(int)); n=per*cores
    for p in parts:
        for t,d in p.items():
            for k,v in d.items(): tot[t][k]+=v
    teams=sorted(tot, key=lambda t:(-tot[t]['champ'],-tot[t]['fin'],-tot[t]['sf']))
    print("#"*86)
    print(f"#  PROYECCION MUNDIAL 2026 — {n:,} torneos simulados ({cores} nucleos)")
    print(f"#  Motor Elo calibrado: TOTAL={TOTAL} GP400={GP400} HOST={HOST} rho={RHO}")
    print("#"*86)
    print(f"\n  {'EQUIPO':22}{'8vos':>7}{'4tos':>7}{'Semis':>7}{'Final':>7}{'CAMPEON':>9}")
    print("  "+"-"*70)
    for t in teams[:24]:
        d=tot[t]
        print(f"  {t:22}{d['r16']/n*100:6.1f}%{d['qf']/n*100:6.1f}%{d['sf']/n*100:6.1f}%{d['fin']/n*100:6.1f}%{d['champ']/n*100:8.1f}%")
    json.dump({t:{k:tot[t][k]/n for k in ('win','2nd','qual','r16','qf','sf','fin','champ')} for t in teams},
              open("tournament_probs.json","w",encoding='utf-8'),ensure_ascii=False,indent=2)
    print("\n  -> tournament_probs.json guardado.")
    print("#"*86)

if __name__=="__main__": main()
