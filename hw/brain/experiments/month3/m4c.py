"""domain shift fix: context banks of dream counts (float sim, 5-bit table, 10-bit scaled counts). usage: DS"""
import sys,time,os; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from feature_layer import Features
from sleep import SurpriseTable
from rate_memory import ScaledCounts
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds=sys.argv[1]
xtr,ytr,xte,yte=load(D,ds); ytr=ytr.astype(int); yte=yte.astype(int)
rot=lambda x: np.rot90(x.reshape(-1,28,28),1,axes=(1,2)).reshape(-1,784).copy()
cache=f"{D}/domain_{ds}.npz"; h=len(xtr)//2
if os.path.exists(cache):
    z=np.load(cache); cA,cB,tU,tR=z["a"],z["b"],z["u"],z["r"]
else:
    fes=[Features(32,thr=c).fit(xtr[np.isin(ytr,(0,1))][:12000]) for c in (50,150,("on",8),("off",8))]
    enc=lambda x: np.concatenate([np.concatenate([f.encode(x[i:i+5000]) for f in fes],1) for i in range(0,len(x),5000)])
    cA,cB,tU,tR=enc(xtr[:h]),enc(rot(xtr[h:])),enc(xte),enc(rot(xte)); np.savez_compressed(cache,a=cA,b=cB,u=tU,r=tR)
yA,yB=ytr[:h],ytr[h:]; NB=cA.shape[1]; allk=np.ones(10,bool)
def run(mode):
    t0=time.time(); st=SurpriseTable(NB,10,cmax=15); bank=ScaledCounts(NB,10,B=10)
    bank.learn(cA,yA); st.practise(cA,yA,allk,seed=0)                       # day 1 (all classes new)
    old=None
    if mode=="live":                                                          # no copy: dream the live (mixed) bank
        old=bank
    if mode in ("banks","snapshot"):
        old=ScaledCounts(NB,10,B=10); old.on=bank.on.copy(); old.n=bank.n.copy()
        if mode=="banks": bank=ScaledCounts(NB,10,B=10)                      # fresh bank for the new context
    bank.learn(cB,yB)
    X,Y=cB,yB
    if old is not None:                                                        # day 2: dreams of yesterday interleaved
        dx,dy=old.dreams(range(10),3000,1); X=np.concatenate([X,dx]); Y=np.concatenate([Y,dy])
    st.practise(X,Y,allk,seed=1)
    dx,dy=bank.dreams(range(10),3000,2)                                        # night
    if old is not None:
        ox,oy=old.dreams(range(10),3000,3); dx=np.concatenate([dx,ox]); dy=np.concatenate([dy,oy])
    st.practise(dx,dy,allk,epochs=2,seed=2)
    u=(st.predict(tU,allk)==yte).mean(); r=(st.predict(tR,allk)==yte).mean()
    print(ds,mode,"after day 2: upright %.4f rotated %.4f mean %.4f"%(u,r,(u+r)/2),"%.0fs"%(time.time()-t0),flush=True)
for mode in ("live",):
    run(mode)
