"""few-shot with spread (population) codes: each active (cell, feature) also lights the same feature in neighbouring
cells (OR over a (2r+1)x(2r+1) cell window). Episodic recall = stored example with the largest overlap (minus half its
size); table = 5-bit surprise table, 10 passes. usage: DS"""
import sys; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from sleep import SurpriseTable
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds=sys.argv[1]
z=np.load(f"{D}/sep_{ds}_F32_p2.npz"); ctr,cte=z["tr"],z["te"]
_,ytr,_,yte=load(D,ds); ytr=ytr.astype(int); yte=yte.astype(int); allk=np.ones(10,bool)
def spread(code,r):
    if r==0: return code
    m=code.reshape(len(code),4,6,6,32); out=np.zeros_like(m)
    p=np.pad(m,((0,0),(0,0),(r,r),(r,r),(0,0)))
    for dy in range(2*r+1):
        for dx in range(2*r+1):
            out|=p[:,:,dy:dy+6,dx:dx+6,:]
    return out.reshape(len(code),-1)
for r in (0,1,2):
    cte_s=spread(cte,r); res={}
    for k in (1,5,20):
        a=[];e=[]
        for s in range(3):
            g=np.random.RandomState(s); idx=np.concatenate([g.choice(np.where(ytr==c)[0],k,replace=False) for c in range(10)])
            ctr_s=spread(ctr[idx],r)
            a.append((SurpriseTable(ctr_s.shape[1],10,cmax=15).practise(ctr_s,ytr[idx],allk,epochs=10,seed=s).predict(cte_s,allk)==yte).mean())
            ov=cte_s.astype(np.int32)@ctr_s.astype(np.int32).T-ctr_s.sum(1)[None]//2
            e.append((ytr[idx][ov.argmax(1)]==yte).mean())
        res[k]=(round(float(np.mean(a)),3),round(float(np.mean(e)),3))
    print(ds,"spread r",r,"active %.0f"%cte_s.sum(1).mean(),"few-shot k: (table, episodic)",res,flush=True)
