"""few-shot fusion (two memory systems, like hippocampus + cortex): episodic recall (best overlap with a stored example
per class) and the surprise table vote together. Both scores are integer: table score and overlap; fused by adding
the table score to (overlap >> s). Spread codes r=1. usage: DS"""
import sys; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from sleep import SurpriseTable
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds=sys.argv[1]
z=np.load(f"{D}/sep_{ds}_F32_p2.npz"); ctr,cte=z["tr"],z["te"]
_,ytr,_,yte=load(D,ds); ytr=ytr.astype(int); yte=yte.astype(int); allk=np.ones(10,bool)
def spread(code,r=1):
    m=code.reshape(len(code),4,6,6,32); out=np.zeros_like(m); p=np.pad(m,((0,0),(0,0),(r,r),(r,r),(0,0)))
    for dy in range(2*r+1):
        for dx in range(2*r+1): out|=p[:,:,dy:dy+6,dx:dx+6,:]
    return out.reshape(len(code),-1)
cte_s=spread(cte)
for k in (1,5,20):
    res={}
    for s in range(3):
        g=np.random.RandomState(s); idx=np.concatenate([g.choice(np.where(ytr==c)[0],k,replace=False) for c in range(10)])
        X=spread(ctr[idx]); Y=ytr[idx]
        st=SurpriseTable(X.shape[1],10,cmax=15).practise(X,Y,allk,epochs=10,seed=s); ts=st.scores(cte_s,allk).astype(np.int64)
        ov=cte_s.astype(np.int32)@X.astype(np.int32).T-X.sum(1)[None]//2
        ep=np.stack([ov[:,Y==c].max(1) for c in range(10)],1).astype(np.int64)
        for name,sc in [("table",ts),("episodic",ep)]+[(f"fused<<{sh}",ts+(ep<<sh)) for sh in (2,3,4,5,6)]:
            res.setdefault(name,[]).append((sc.argmax(1)==yte).mean())
    print(ds,"k",k,{n:round(float(np.mean(v)),3) for n,v in res.items()},flush=True)
