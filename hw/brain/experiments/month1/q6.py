import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from feature_layer import Features, CountMemory
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds=sys.argv[1]
xtr,ytr,xte,yte=load(D,ds); ytr=ytr.astype(int); yte=yte.astype(int)
for F in (32,64,128):
    t=time.time(); fe=Features(F).fit(xtr[:20000]); ctr=np.concatenate([fe.encode(xtr[i:i+5000]) for i in range(0,60000,5000)]); cte=fe.encode(xte)
    m=CountMemory(ctr.shape[1],10).learn(ctr,ytr)
    res={a:(m.predict(cte,alpha=a)==yte).mean() for a in (0.1,1,5)}
    print(ds,"F",F,"bits",ctr.shape[1],"active/img %.0f"%ctr.sum(1).mean(),"acc",res,"%.0fs"%(time.time()-t),flush=True)
    for k in (1,5,20):
        a=[]
        for s in range(3):
            r=np.random.RandomState(s); idx=np.concatenate([r.choice(np.where(ytr==c)[0],k,replace=False) for c in range(10)])
            a.append((CountMemory(ctr.shape[1],10).learn(ctr[idx],ytr[idx]).predict(cte,alpha=1)==yte).mean())
        print("  few-shot",k,"%.4f"%np.mean(a),flush=True)
