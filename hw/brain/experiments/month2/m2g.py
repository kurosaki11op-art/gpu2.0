"""continual fast table without dreams: local competition + homeostatic scaling. usage: DS F"""
import sys; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
import cochlea
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds,F=sys.argv[1],int(sys.argv[2])
z=np.load(f"{D}/sep_{ds}_F{F}_p2.npz"); ctr,cte=z["tr"],z["te"]
if ds=="speech": _,ytr,_,yte=cochlea.load_speech(D+"/speech",D+"/speech_pics_res.npz",cochlea.sound_picture_res)
else: _,ytr,_,yte=load(D,ds)
ytr=ytr.astype(int); yte=yte.astype(int); NB=ctr.shape[1]
stages=[(0,1),(2,3),(4,5),(6,7),(8,9)]
def run(local, homeo, cmax, margin=8, epochs=3):
    W=np.zeros((10,NB),np.int32); bias=np.zeros(10); known=np.zeros(10,bool); res=[]
    for i,s in enumerate(stages):
        sel=np.where(np.isin(ytr,s))[0]; known[list(s)]=True
        comp=np.zeros(10,bool); comp[list(s)]=True
        if not local: comp=known.copy()
        r=np.random.RandomState(i)
        for ep in range(epochs):
            o=r.permutation(sel)
            for j in range(0,len(o),50):
                idx=o[j:j+50]; c=ctr[idx].astype(np.int32); y=ytr[idx]; ar=np.arange(len(idx))
                sc=c@W.T; sc[:,~comp]=-10**9; t=sc[ar,y].copy(); sc[ar,y]=-10**9; rv=sc.argmax(1)
                sup=(t-sc[ar,rv])<=margin
                np.add.at(W,y[sup],c[sup]); np.subtract.at(W,rv[sup],c[sup]); np.clip(W,-cmax,cmax,out=W)
        if homeo:   # each class's typical response to its own examples is pinned to 0 (one number per class)
            for k in s:
                bias[k]=-(ctr[ytr==k][:2000].astype(np.int32)@W[k]).mean()
        seen=np.isin(yte,np.where(known)[0])
        sc=cte[seen].astype(np.int32)@W.T+bias; sc[:,~known]=-10**9
        res.append((sc.argmax(1)==yte[seen]).mean())
    return res
for local,homeo in [(0,0),(1,0),(1,1)]:
    for cmax in (15,127):
        print(ds,"local",local,"homeo",homeo,"cmax",cmax,np.round(run(local,homeo,cmax),4),flush=True)
