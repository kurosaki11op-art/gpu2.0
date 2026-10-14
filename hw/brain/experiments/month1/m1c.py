import sys,time,json,os; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from feature_layer import Features, ConceptMemory
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds=sys.argv[1]; P=int(sys.argv[2])
cache=f"{D}/codes_{ds}.npz"
xtr,ytr,xte,yte=load(D,ds); ytr=ytr.astype(int); yte=yte.astype(int)
if os.path.exists(cache):
    z=np.load(cache); ctr,cte=z["tr"],z["te"]
else:
    src=xtr[np.isin(ytr,(0,1))][:12000]
    fes=[Features(128,thr=c).fit(src) for c in (50,150,("on",8),("off",8))]
    enc=lambda x: np.concatenate([np.concatenate([f.encode(x[i:i+5000]) for f in fes],1) for i in range(0,len(x),5000)])
    ctr,cte=enc(xtr),enc(xte); np.savez_compressed(cache,tr=ctr,te=cte)
t0=time.time()
for a in (0.5,):
    m=ConceptMemory(ctr.shape[1],10,P=P,alpha=a).learn(ctr,ytr)
    print(ds,"P",P,"alpha",a,"concept memory %.4f"%(m.predict(cte)==yte).mean(),"%.0fs"%(time.time()-t0),flush=True)
