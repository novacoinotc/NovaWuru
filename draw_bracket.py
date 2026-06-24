#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dibuja el bracket del Mundial 2026 (datos de bracket_played.json) en PNG y PDF."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

B=json.load(open("bracket_played.json",encoding='utf-8'))
ABBR={"Bosnia and Herzegovina":"Bosnia","South Korea":"S. Korea","South Africa":"S. Africa",
      "Ivory Coast":"I. Coast","Saudi Arabia":"Saudi Ar.","New Zealand":"N. Zealand",
      "Cabo Verde":"Cabo V.","Netherlands":"Netherl.","Switzerland":"Switzerl.","Czechia":"Czechia",
      "United States":"USA","DR Congo":"DR Congo","Uzbekistan":"Uzbek."}
def ab(t): return ABBR.get(t,t)

# estructura del arbol (indices de R32 -> R16 -> QF -> SF)
L_R32=[0,2,1,4,10,11,8,9]; R_R32=[3,5,6,7,13,15,12,14]
L_R16=[0,1,4,5]; R_R16=[2,3,6,7]
L_QF=[0,1]; R_QF=[2,3]

GREEN="#1b8a3a"; GREY="#9aa0a6"; BOX="#f5f7fa"; EDGE="#c2c8d0"; HL="#fff7cc"

fig,ax=plt.subplots(figsize=(24,13.5)); ax.axis("off")
ax.set_xlim(0,24); ax.set_ylim(0,15)
BW,BH=2.5,0.92   # ancho/alto caja
XCOL=[0.3,3.2,6.1,9.0, 11.9, 14.6,17.5,20.4]  # L:R32,R16,QF,SF ; R:SF,QF,R16,R32 (center final aparte)
def ys(n):
    top,bot=14.2,0.8;
    return [top-(top-bot)*(i)/(n-1) if n>1 else (top+bot)/2 for i in range(n)]

def draw_match(x,y,m,flip=False):
    w_home = (m['winner']==m['home'])
    box=FancyBboxPatch((x,y-BH/2),BW,BH,boxstyle="round,pad=0.02,rounding_size=0.08",
                       fc=BOX,ec=EDGE,lw=1.2,zorder=2)
    ax.add_patch(box)
    ax.plot([x,x+BW],[y,y],color=EDGE,lw=0.8,zorder=3)
    note=""
    if m.get('pen'): note=" p"
    elif m.get('et'): note=" e"
    rows=[(m['home'],m['gh'],w_home),(m['away'],m['ga'],not w_home)]
    for j,(t,g,win) in enumerate(rows):
        yy=y+ (BH*0.25 if j==0 else -BH*0.25)
        col=GREEN if win else GREY; fw='bold' if win else 'normal'
        ax.text(x+0.12,yy,ab(t),ha='left',va='center',fontsize=10.5,color=col,fontweight=fw,zorder=4)
        ax.text(x+BW-0.15,yy,str(g)+(note if (win and (m.get('pen')or m.get('et')) and j==0) else ''),
                ha='right',va='center',fontsize=10.5,color=col,fontweight=fw,zorder=4)
    return (x, y, x+BW, y)

def connect(p1,p2,xnext):
    # codo desde salida de match (x2,y) al inicio del siguiente
    for (x1l,y1,x1r,_) in (p1,p2):
        ax.plot([x1r,xnext],[y1,y1],color=EDGE,lw=1.0,zorder=1)
    my=(p1[1]+p2[1])/2
    ax.plot([xnext,xnext],[p1[1],p2[1]],color=EDGE,lw=1.0,zorder=1)
    return my

# ---- posiciones ----
# LEFT R32
ly32=ys(8); pos={}
for k,idx in enumerate(L_R32): pos[('L32',idx)]=draw_match(XCOL[0],ly32[k],B['R32'][idx])
# LEFT R16
ly16=[ (pos[('L32',L_R32[2*k])][1]+pos[('L32',L_R32[2*k+1])][1])/2 for k in range(4)]
for k,idx in enumerate(L_R16):
    p1=pos[('L32',L_R32[2*k])]; p2=pos[('L32',L_R32[2*k+1])]
    connect(p1,p2,XCOL[1]-0.15)
    pos[('L16',idx)]=draw_match(XCOL[1],ly16[k],B['R16'][idx])
# LEFT QF
lyqf=[ (pos[('L16',L_R16[2*k])][1]+pos[('L16',L_R16[2*k+1])][1])/2 for k in range(2)]
for k,idx in enumerate(L_QF):
    p1=pos[('L16',L_R16[2*k])]; p2=pos[('L16',L_R16[2*k+1])]; connect(p1,p2,XCOL[2]-0.15)
    pos[('LQF',idx)]=draw_match(XCOL[2],lyqf[k],B['QF'][idx])
# LEFT SF
lysf=(pos[('LQF',0)][1]+pos[('LQF',1)][1])/2
connect(pos[('LQF',0)],pos[('LQF',1)],XCOL[3]-0.15)
pos[('LSF',0)]=draw_match(XCOL[3],lysf,B['SF'][0])

# RIGHT R32 (dibujadas alineadas a la derecha)
ry32=ys(8)
for k,idx in enumerate(R_R32): pos[('R32',idx)]=draw_match(XCOL[7],ry32[k],B['R32'][idx])
ry16=[ (pos[('R32',R_R32[2*k])][1]+pos[('R32',R_R32[2*k+1])][1])/2 for k in range(4)]
for k,idx in enumerate(R_R16):
    p1=pos[('R32',R_R32[2*k])]; p2=pos[('R32',R_R32[2*k+1])]
    # conexion hacia la izquierda
    for (x1l,y1,x1r,_) in (p1,p2): ax.plot([x1l,XCOL[6]+BW+0.15],[y1,y1],color=EDGE,lw=1.0,zorder=1)
    ax.plot([XCOL[6]+BW+0.15,XCOL[6]+BW+0.15],[p1[1],p2[1]],color=EDGE,lw=1.0,zorder=1)
    pos[('R16',idx)]=draw_match(XCOL[6],ry16[k],B['R16'][idx])
ryqf=[ (pos[('R16',R_R16[2*k])][1]+pos[('R16',R_R16[2*k+1])][1])/2 for k in range(2)]
for k,idx in enumerate(R_QF):
    p1=pos[('R16',R_R16[2*k])]; p2=pos[('R16',R_R16[2*k+1])]
    for (x1l,y1,x1r,_) in (p1,p2): ax.plot([x1l,XCOL[5]+BW+0.15],[y1,y1],color=EDGE,lw=1.0,zorder=1)
    ax.plot([XCOL[5]+BW+0.15,XCOL[5]+BW+0.15],[p1[1],p2[1]],color=EDGE,lw=1.0,zorder=1)
    pos[('RQF',idx)]=draw_match(XCOL[5],ryqf[k],B['QF'][idx])
rysf=(pos[('RQF',2)][1]+pos[('RQF',3)][1])/2
for (x1l,y1,x1r,_) in (pos[('RQF',2)],pos[('RQF',3)]): ax.plot([x1l,XCOL[4]+BW+0.15],[y1,y1],color=EDGE,lw=1.0,zorder=1)
ax.plot([XCOL[4]+BW+0.15,XCOL[4]+BW+0.15],[pos[('RQF',2)][1],pos[('RQF',3)][1]],color=EDGE,lw=1.0,zorder=1)
pos[('RSF',0)]=draw_match(XCOL[7]-0.0 if False else XCOL[7]*0+XCOL[4]+0,0,B['SF'][1]) if False else None
pos[('RSF',0)]=draw_match(XCOL[4]+0,rysf,B['SF'][1]) if False else None
# SF derecha en su columna (entre QF derecha y final)
XR_SF=XCOL[4]  # reutilizamos? mejor poner SF derecha en x propia
pos[('RSF',0)]=None

# Final al centro
XF=11.4; yf=7.5
# colocar SF izquierda ya esta; SF derecha:
RSF_x=14.0
pos[('RSF',0)]=draw_match(RSF_x,rysf,B['SF'][1])
# conectar QF derecha -> SF derecha
for (x1l,y1,x1r,_) in (pos[('RQF',2)],pos[('RQF',3)]): ax.plot([x1l,RSF_x+BW+0.15],[y1,y1],color=EDGE,lw=1.0,zorder=1)
ax.plot([RSF_x+BW+0.15,RSF_x+BW+0.15],[pos[('RQF',2)][1],pos[('RQF',3)][1]],color=EDGE,lw=1.0,zorder=1)
# Final
fmatch=B['Final'][0]
# lineas SF -> final
ax.plot([pos[('LSF',0)][2],XF],[pos[('LSF',0)][1],pos[('LSF',0)][1]],color=EDGE,lw=1.0)
ax.plot([pos[('RSF',0)][0],XF+BW],[pos[('RSF',0)][1],pos[('RSF',0)][1]],color=EDGE,lw=1.0)
draw_match(XF,yf,fmatch)
ax.text(XF+BW/2, yf+1.2, "FINAL", ha='center',fontsize=13,fontweight='bold',color="#222")

# Campeon banner
champ=B['champion']
ax.add_patch(FancyBboxPatch((XF-0.1,yf-2.6),BW+0.2,1.0,boxstyle="round,pad=0.02,rounding_size=0.1",
            fc="#ffd24d",ec="#caا000" if False else "#b8860b",lw=2,zorder=5))
ax.text(XF+BW/2, yf-2.1, f"★ CAMPEON: {ab(champ)}", ha='center',va='center',fontsize=14,fontweight='bold',color="#5a3e00",zorder=6)

# etiquetas de ronda
labels=[("16avos",XCOL[0]),("8vos",XCOL[1]),("4tos",XCOL[2]),("Semis",XCOL[3]),
        ("Semis",RSF_x),("4tos",XCOL[5]),("8vos",XCOL[6]),("16avos",XCOL[7])]
for txt,x in labels: ax.text(x+BW/2,14.8,txt,ha='center',fontsize=12,fontweight='bold',color="#444")

fig.suptitle("MUNDIAL 2026 — Bracket simulado (modelo maestro, partido por partido)   ·   e=tiempo extra · p=penales",
             fontsize=16,fontweight='bold',y=0.985)
plt.tight_layout(rect=[0,0,1,0.96])
fig.savefig("bracket_mundial2026.png",dpi=160,bbox_inches="tight")
fig.savefig("bracket_mundial2026.pdf",bbox_inches="tight")
print("Generados: bracket_mundial2026.png y bracket_mundial2026.pdf")
print("Campeon:",champ)
