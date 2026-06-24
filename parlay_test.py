#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TEST DE LA HIPOTESIS DEL PARLEY:
  "Sacar los picks con ALTA prob de ganar (segun simulacion) y combinarlos en parley de 3-4
   -> ganamos todos -> duplicamos facil."
Se prueba sobre 28 partidos del Mundial YA JUGADOS (prob real del modelo + resultado real).
Momios = proxy Elo con jugo (overround 6%), igual que el otro backtest.
"""
import json, math, random
random.seed(7)
BT = json.load(open("backtest.json"))
ELO = json.load(open("elo.json"))
fixtures = {(f["home"], f["away"]): f for f in BT["fixtures"]}

def poisson_1x2(lh, la, maxg=10):
    ph=pd=pa=0.0
    for i in range(maxg+1):
        for j in range(maxg+1):
            p=(math.exp(-lh)*lh**i/math.factorial(i))*(math.exp(-la)*la**j/math.factorial(j))
            if i>j: ph+=p
            elif i==j: pd+=p
            else: pa+=p
    return ph,pd,pa
def market(home,away,host):
    eh,ea=ELO.get(home,1600),ELO.get(away,1600); hfa=70 if host and host.lower()==home.lower() else 0
    sup=((eh+hfa)-ea)/130.0; lh=max(0.15,(2.6+sup)/2); la=max(0.15,(2.6-sup)/2); return poisson_1x2(lh,la)
def vig(probs,ov=1.06):
    s=sum(probs); return [1.0/(p/s*ov) for p in probs]

LBL=["H","D","A"]
def won(sel,f): hg,ag=f["hg"],f["ag"]; return (sel=="H" and hg>ag) or (sel=="A" and ag>hg) or (sel=="D" and hg==ag)

# Para cada partido: pick FAVORITO DEL MODELO (mas prob), su momio, su prob modelo, si gano de verdad
PICKS=[]
for p in BT["predictions"]:
    f=fixtures.get((p["home"],p["away"]))
    if not f: continue
    model=[p["p_home"],p["p_draw"],p["p_away"]]
    odds=vig(market(p["home"],p["away"],f.get("host","")))
    i=max(range(3),key=lambda k:model[k])   # el que el modelo dice que GANA
    PICKS.append({"name":f"{p['home']} vs {p['away']}","sel":LBL[i],"prob":model[i],"odds":odds[i],"won":won(LBL[i],f)})

n=len(PICKS); hit=sum(p["won"] for p in PICKS)
print(f"\n{'='*70}\nTEST HIPOTESIS PARLEY · {n} partidos Mundial ya jugados\n{'='*70}")
print(f"Pick = el que el MODELO dice que gana (mas prob).")
print(f"  Prob promedio de esos picks: {sum(p['prob'] for p in PICKS)/n*100:.0f}%")
print(f"  % que GANARON de verdad (singles): {hit/n*100:.0f}%  ({hit}/{n})")
print(f"  Momio promedio de esos picks: {sum(p['odds'] for p in PICKS)/n:.2f}")

def boot_parlay(nlegs, min_prob=0.0, B=20000):
    """Arma parleys aleatorios de nlegs picks (modelo-ganador) con prob>=min_prob. Stake 100."""
    pool=[p for p in PICKS if p["prob"]>=min_prob]
    if len(pool)<nlegs: return None
    allwin=0; bank=0.0; staked=0.0
    for _ in range(B):
        legs=random.sample(pool,nlegs)
        codds=1.0; ok=True
        for l in legs:
            codds*=l["odds"]; ok=ok and l["won"]
        staked+=100
        if ok: allwin+=1; bank+=100*(codds-1)
        else: bank-=100
    return {"hit":allwin/B, "roi":bank/staked, "avgmult":sum(1 for _ in range(0))}

print(f"\n{'='*70}\nPARLEYS de FAVORITOS DEL MODELO (a momios de mercado, 20k simulaciones)\n{'='*70}")
print(f"{'Tipo':<38}{'% gana TODO':>12}{'ROI':>10}")
for nlegs in (2,3,4):
    r=boot_parlay(nlegs)
    print(f"Parley {nlegs} legs (cualquier favorito)     {r['hit']*100:>10.1f}% {r['roi']*100:>8.1f}%")
for nlegs in (3,4):
    r=boot_parlay(nlegs,min_prob=0.55)
    if r: print(f"Parley {nlegs} legs (solo prob>=55%)       {r['hit']*100:>10.1f}% {r['roi']*100:>8.1f}%")
for nlegs in (3,4):
    r=boot_parlay(nlegs,min_prob=0.65)
    if r: print(f"Parley {nlegs} legs (solo prob>=65%)       {r['hit']*100:>10.1f}% {r['roi']*100:>8.1f}%")

# Comparacion: parley de VALOR (solo legs +EV) vs singles de valor
def boot_value_parlay(nlegs,B=20000):
    pool=[p for p in PICKS if p["prob"]*p["odds"]-1>0.03]  # solo legs con valor (edge>3%)
    if len(pool)<nlegs: return None
    allwin=0; bank=0.0
    for _ in range(B):
        legs=random.sample(pool,nlegs); codds=1.0; ok=True
        for l in legs: codds*=l["odds"]; ok=ok and l["won"]
        bank+= 100*(codds-1) if ok else -100
    return {"hit":allwin/B,"roi":bank/(100*B),"pool":len(pool)}
print(f"\n{'='*70}\nPARLEYS de VALOR (solo legs con edge>3%) vs SINGLES de valor\n{'='*70}")
for nlegs in (2,3):
    r=boot_value_parlay(nlegs)
    if r: print(f"Parley VALOR {nlegs} legs (pool {r['pool']})         ROI {r['roi']*100:>6.1f}%")
# singles de valor
vp=[p for p in PICKS if p["prob"]*p["odds"]-1>0.03]
if vp:
    roi=sum((p["odds"]-1) if p["won"] else -1 for p in vp)/len(vp)
    print(f"SINGLES de valor ({len(vp)} apuestas)            ROI {roi*100:>6.1f}%  (% acierto {sum(x['won'] for x in vp)/len(vp)*100:.0f}%)")
