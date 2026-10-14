import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from feature_layer import Features, CountMemory
from sleep import SurpriseTable, dreams
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds=sys.argv[1]; F=int(sys.argv[2]); thrs=tuple(int(t) for t in sys.argv[3].split(","))
xtr,ytr,xte,yte=load(D,ds); ytr=ytr.astype(int); yte=yte.astype(int)
stages=[(0,1),(2,3),(4,5),(6,7),(8,9)]
t0=time.time(); src=xtr[np.isin(ytr,stages[0])][:12000]
fes=[Features(F,thr=t).fit(src) for t in thrs]
enc=lambda x: np.concatenate([np.concatenate([f.encode(x[i:i+5000]) for f in fes],1) for i in range(0,len(x),5000)])
ctr,cte=enc(xtr),enc(xte); NB=ctr.shape[1]; allk=np.ones(10,bool)
print(ds,F,thrs,"bits",NB,"%.0fs"%(time.time()-t0),flush=True)
cm=CountMemory(NB,10).learn(ctr,ytr); print(" count memory, all at once %.4f"%(cm.predict(cte)==yte).mean(),flush=True)
st=SurpriseTable(NB,10).practise(ctr,ytr,allk); print(" surprise table, all at once %.4f"%(st.predict(cte)==yte).mean(),flush=True)
# continual: stable count memory + surprise table with / without dreams
for mode in ("no-sleep","sleep"):
    cm3=CountMemory(NB,10); st3=SurpriseTable(NB,10); known=np.zeros(10,bool)
    for i,s in enumerate(stages):
        sel=np.isin(ytr,s); cm3.learn(ctr[sel],ytr[sel]); old=np.where(known)[0]; known[list(s)]=True
        X,Y=ctr[sel],ytr[sel]
        if mode=="sleep" and len(old):
            dx,dy=dreams(cm3,old,6000,seed=i); X=np.concatenate([X,dx]); Y=np.concatenate([Y,dy])
        st3.practise(X,Y,known,seed=i)
        seen=np.isin(yte,np.where(known)[0])
        print("  %s stage %d: table %.4f  count %.4f"%(mode,i+1,(st3.predict(cte[seen],known)==yte[seen]).mean(),(cm3.predict(cte[seen])==yte[seen]).mean()),flush=True)
print("done %.0fs"%(time.time()-t0))
