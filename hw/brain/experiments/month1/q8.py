import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from feature_layer import Features, CountMemory
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
xtr,ytr,xte,yte=load(D,"fashion"); ytr=ytr.astype(int); yte=yte.astype(int)
def run(F,thrs,src):
    codes_tr,codes_te=[],[]
    for th in thrs:
        fe=Features(F,thr=th).fit(src)
        codes_tr.append(np.concatenate([fe.encode(xtr[i:i+5000]) for i in range(0,60000,5000)])); codes_te.append(fe.encode(xte))
    ctr,cte=np.concatenate(codes_tr,1),np.concatenate(codes_te,1)
    m=CountMemory(ctr.shape[1],10).learn(ctr,ytr); nb=(m.predict(cte)==yte).mean()
    # surprise-gated correction table on top (int8 per class per bit; +1 true / -1 rival when margin small)
    W=np.zeros((10,ctr.shape[1]),np.int32); r=np.random.RandomState(0)
    for ep in range(3):
        for i in range(0,60000,50):
            idx=r.permutation(60000)[:50] if False else np.arange(i,i+50)
            c=ctr[idx].astype(np.int32); s=c@W.T; y=ytr[idx]; t=s[np.arange(50),y].copy(); s[np.arange(50),y]=-10**9; rv=s.argmax(1)
            sup=(t-s[np.arange(50),rv])<=8
            np.add.at(W,y[sup],c[sup]); np.subtract.at(W,rv[sup],c[sup]); np.clip(W,-127,127,out=W)
    sg=((cte.astype(np.int32)@W.T).argmax(1)==yte).mean()
    print("F",F,"thr",thrs,"bits",ctr.shape[1],"count-memory %.4f  surprise-table %.4f"%(nb,sg),flush=True)
run(128,(100,),xtr[np.isin(ytr,(0,1))][:12000])
run(128,(100,),xtr[:20000])
run(128,(50,150),xtr[:20000])
