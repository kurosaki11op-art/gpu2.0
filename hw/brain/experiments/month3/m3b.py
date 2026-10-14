"""few-shot vs where the sensory detectors learned (unlabeled): stage-1 images only vs a broad unlabeled set.
Learner: fast table, 10 passes over the k examples (float sim), and episodic recall. usage: DS"""
import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np, torch
from cortex_core import load
from feature_layer import Features
from sleep import SurpriseTable
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds=sys.argv[1]
xtr,ytr,xte,yte=load(D,ds); ytr=ytr.astype(int); yte=yte.astype(int); allk=np.ones(10,bool)
CH=(50,150,("on",8),("off",8))
def codes(src,F):
    fes=[Features(F,thr=c).fit(src) for c in CH]
    enc=lambda x: np.concatenate([np.concatenate([f.encode(x[i:i+5000]) for f in fes],1) for i in range(0,len(x),5000)])
    return enc
r0=np.random.RandomState(9)
for name,src,F in [("stage1-only",xtr[np.isin(ytr,(0,1))][:12000],32),("broad-unlabeled",xtr[r0.choice(60000,12000,replace=False)],32),
                   ("broad-unlabeled F64",xtr[r0.choice(60000,12000,replace=False)],64)]:
    t0=time.time(); enc=codes(src,F); cte=enc(xte); NB=cte.shape[1]; out={}
    for k in (1,5,20):
        a=[];e=[]
        for s in range(3):
            r=np.random.RandomState(s); idx=np.concatenate([r.choice(np.where(ytr==c)[0],k,replace=False) for c in range(10)])
            ctr=enc(xtr[idx])
            a.append((SurpriseTable(NB,10,cmax=15).practise(ctr,ytr[idx],allk,epochs=10,seed=s).predict(cte,allk)==yte).mean())
            ov=cte.astype(np.int32)@ctr.astype(np.int32).T-ctr.sum(1)[None]//2
            e.append((ytr[idx][ov.argmax(1)]==yte).mean())
        out[k]=(round(float(np.mean(a)),4),round(float(np.mean(e)),4))
    print(ds,name,"bits",NB,"few-shot k: (table, episodic)",out,"%.0fs"%(time.time()-t0),flush=True)
