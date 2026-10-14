"""chip-honest rate memory (B bits, shift k, stochastic rounding) as dream source, night2 sleep. usage: DS F"""
import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from rate_memory import RateMemory
from sleep import SurpriseTable
import cochlea
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds,F=sys.argv[1],int(sys.argv[2])
z=np.load(f"{D}/sep_{ds}_F{F}_p2.npz"); ctr,cte=z["tr"],z["te"]
if ds=="speech": _,ytr,_,yte=cochlea.load_speech(D+"/speech",D+"/speech_pics_res.npz",cochlea.sound_picture_res)
else: _,ytr,_,yte=load(D,ds)
ytr=ytr.astype(int); yte=yte.astype(int); NB=ctr.shape[1]
stages=[(0,1),(2,3),(4,5),(6,7),(8,9)]
def run(B,k,nd=6000,cmax=15,kmax=None):
    t0=time.time(); st=SurpriseTable(NB,10,cmax=cmax); known=np.zeros(10,bool); res=[]; mem=RateMemory(NB,10,B=B,k=k,kmax=kmax)
    for i,s in enumerate(stages):
        sel=np.isin(ytr,s); mem.learn(ctr[sel],ytr[sel]); old=np.where(known)[0]; known[list(s)]=True
        X,Y=ctr[sel],ytr[sel]
        if len(old):
            dx,dy=mem.dreams(old,nd,i); X=np.concatenate([X,dx]); Y=np.concatenate([Y,dy])
        st.practise(X,Y,known,seed=i)
        if i>0:
            dx,dy=mem.dreams(np.where(known)[0],nd,100+i); st.practise(dx,dy,known,epochs=2,seed=100+i)
        seen=np.isin(yte,np.where(known)[0]); res.append((st.predict(cte[seen],known)==yte[seen]).mean())
    print(ds,"rate B",B,"k",k,"kmax",kmax,"KB %.0f"%(mem.bits()/8192),np.round(res,4),"%.0fs"%(time.time()-t0),flush=True)
for B,kmax in [(8,12),(8,9),(6,9)]:
    run(B,0,kmax=kmax)
