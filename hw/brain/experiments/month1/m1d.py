import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from feature_layer import ConceptMemory
from sleep import SurpriseTable
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds=sys.argv[1]; P=int(sys.argv[2]); ND=int(sys.argv[3])
z=np.load(f"{D}/codes_{ds}.npz"); ctr,cte=z["tr"],z["te"]
_,ytr,_,yte=load(D,ds); ytr=ytr.astype(int); yte=yte.astype(int)
stages=[(0,1),(2,3),(4,5),(6,7),(8,9)]; NB=ctr.shape[1]; t0=time.time()
cm=ConceptMemory(NB,10,P=P); st=SurpriseTable(NB,10); known=np.zeros(10,bool)
for i,s in enumerate(stages):
    sel=np.isin(ytr,s); cm.learn(ctr[sel],ytr[sel]); old=np.where(known)[0]; known[list(s)]=True
    X,Y=ctr[sel],ytr[sel]
    if len(old):
        dx,dy=cm.dreams(old,ND,seed=i); X=np.concatenate([X,dx]); Y=np.concatenate([Y,dy])
    st.practise(X,Y,known,seed=i)
    seen=np.isin(yte,np.where(known)[0])
    sc=cm.scores(cte[seen]); sc[:,~known]=-1e30; tb=st.scores(cte[seen],known)
    # combined: concept memory picks top-2, table breaks the tie (no score scaling needed)
    top2=np.argsort(-sc,1)[:,:2]; tv=np.take_along_axis(tb,top2,1); comb=top2[np.arange(len(top2)),tv.argmax(1)]
    print("%s P%d dreams%d stage %d: concept %.4f table %.4f combined %.4f  %.0fs"%(ds,P,ND,i+1,(sc.argmax(1)==yte[seen]).mean(),(tb.argmax(1)==yte[seen]).mean(),(comb==yte[seen]).mean(),time.time()-t0),flush=True)
