#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Corre el motor sobre todos los match_*.json y escribe predictions.json (probabilidades por mercado) para la app de paper trading."""
import json, glob, numpy as np
from sim_match import arr, base_idx, elo_base_lams, worker
from collections import Counter

LEAGUE="Mundial 2026"
def metrics(M, n=100000):
    AH=arr(M['home']['players']); AA=arr(M['away']['players'])
    bh=base_idx(AH); ba=base_idx(AA)
    meta=M['meta']; env=M.get('env') or {}
    hh=meta.get('host')==meta.get('home'); ha=meta.get('host')==meta.get('away')
    elH,elA=elo_base_lams(meta['home'],meta['away'],hh,ha)
    gm,ga,_,_=worker((AH,AA,env,hh,ha,n,7,bh,ba,elH,elA))
    tot=gm+ga
    pH=float(np.mean(gm>ga)); pD=float(np.mean(gm==ga)); pA=float(np.mean(gm<ga))
    over=float(np.mean(tot>=3)); under=1-over
    btts=float(np.mean((gm>=1)&(ga>=1))); nbtts=1-btts
    return dict(home=meta['home'],away=meta['away'],group=meta.get('group',''),
        markets=[
            {"market":"1X2","selection":meta['home'],"prob":pH},
            {"market":"1X2","selection":"Empate","prob":pD},
            {"market":"1X2","selection":meta['away'],"prob":pA},
            {"market":"O/U 2.5","selection":"Over 2.5","prob":over},
            {"market":"O/U 2.5","selection":"Under 2.5","prob":under},
            {"market":"BTTS","selection":"BTTS Si","prob":btts},
            {"market":"BTTS","selection":"BTTS No","prob":nbtts},
        ])

def main():
    out=[]
    for f in sorted(glob.glob("match_*.json")):
        M=json.load(open(f,encoding='utf-8'))
        if len(M.get('home',{}).get('players',[]))!=11 or len(M.get('away',{}).get('players',[]))!=11: continue
        mid=f.replace("match_","").replace(".json","")
        m=metrics(M); m['id']=mid; m['league']=LEAGUE; m['sport']='Futbol'
        out.append(m)
        print(f"  {mid}: {m['home']} vs {m['away']}")
    json.dump(out,open("predictions.json","w",encoding='utf-8'),ensure_ascii=False,indent=2)
    print(f"predictions.json -> {len(out)} partidos")

if __name__=="__main__": main()
