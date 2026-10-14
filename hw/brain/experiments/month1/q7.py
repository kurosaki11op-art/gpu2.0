import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from feature_layer import Features, CountMemory
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds=sys.argv[1]; F=int(sys.argv[2])
xtr,ytr,xte,yte=load(D,ds); ytr=ytr.astype(int); yte=yte.astype(int)
enc=lambda fe,x: np.concatenate([fe.encode(x[i:i+5000]) for i in range(0,len(x),5000)])
# features learned only from stage-1 data (classes 0,1), unlabeled
s1=np.isin(ytr,(0,1))
fe=Features(F).fit(xtr[s1][:12000]); ctr=enc(fe,xtr); cte=enc(fe,xte)
print(ds,F,"features from classes 0-1 only -> all-class acc %.4f"%(CountMemory(ctr.shape[1],10).learn(ctr,ytr).predict(cte)==yte).mean(),flush=True)
fe=Features(F).fit(xtr[:20000]); ctr=enc(fe,xtr); cte=enc(fe,xte)
# episodic recall (hippocampus): store codes, answer = label of stored episode with most overlapping active bits
for k in (1,5,20):
    a=[];b=[]
    for s in range(3):
        r=np.random.RandomState(s); idx=np.concatenate([r.choice(np.where(ytr==c)[0],k,replace=False) for c in range(10)])
        ov=cte.astype(np.int32)@ctr[idx].astype(np.int32).T          # sim of AND+popcount
        a.append((ytr[idx][ov.argmax(1)]==yte).mean())
        px=(xte>100).astype(np.int32); pt=(xtr[idx]>100).astype(np.int32)
        b.append((ytr[idx][(px@pt.T - 0.5*pt.sum(1)).argmax(1)]==yte).mean())
    print("  few-shot",k,"episodic-on-features %.4f   episodic-on-raw-pixels %.4f"%(np.mean(a),np.mean(b)),flush=True)
