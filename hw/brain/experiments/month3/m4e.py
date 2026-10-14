"""dendritic conjunctions: within each pooled cell, every pair of active features from different channels is hashed
(XOR of two fixed random 13-bit labels) into one of H extra code bits. Table (5-bit) on [code + conjunction bits],
all at once and 5 stages with scaled-count dreams + night. usage: DS H"""
import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from sleep import SurpriseTable
from rate_memory import ScaledCounts
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds,H=sys.argv[1],int(sys.argv[2])
z=np.load(f"{D}/sep_{ds}_F32_p2.npz"); ctr,cte=z["tr"],z["te"]
_,ytr,_,yte=load(D,ds); ytr=ytr.astype(int); yte=yte.astype(int)
lab=np.random.RandomState(5).randint(0,1<<13,size=(4608,)).astype(np.int64)
def conj(code):
    m=code.reshape(len(code),4,36,32)                         # channel, cell, feature
    out=np.zeros((len(code),H),bool)
    for c1 in range(4):
        for c2 in range(c1+1,4):
            b1,cell1,f1=np.nonzero(m[:,c1]);
            a1={}
            for b,ce,f in zip(b1,cell1,f1): a1.setdefault((b,ce),[]).append(c1*1152+ce*32+f)
            b2,cell2,f2=np.nonzero(m[:,c2])
            for b,ce,f in zip(b2,cell2,f2):
                for i1 in a1.get((b,ce),()):
                    out[b,(lab[i1]^(lab[c2*1152+ce*32+f]*3))%H]=True
    return out
t0=time.time()
qtr=np.concatenate([conj(ctr[i:i+5000]) for i in range(0,len(ctr),5000)]); qte=conj(cte)
print(ds,"H",H,"conj active/img %.0f"%qtr.sum(1).mean(),"%.0fs"%(time.time()-t0),flush=True)
for name,(A,B) in {"code":(ctr,cte),"code+conj":(np.concatenate([ctr,qtr],1),np.concatenate([cte,qte],1))}.items():
    NB=A.shape[1]; allk=np.ones(10,bool)
    aa=(SurpriseTable(NB,10,cmax=15).practise(A,ytr,allk).predict(B,allk)==yte).mean()
    st=SurpriseTable(NB,10,cmax=15); mem=ScaledCounts(NB,10,B=10); known=np.zeros(10,bool)
    for i,s in enumerate([(0,1),(2,3),(4,5),(6,7),(8,9)]):
        sel=np.isin(ytr,s); mem.learn(A[sel],ytr[sel]); old=np.where(known)[0]; known[list(s)]=True; X,Y=A[sel],ytr[sel]
        if len(old):
            dx,dy=mem.dreams(old,6000,i); X=np.concatenate([X,dx]); Y=np.concatenate([Y,dy])
        st.practise(X,Y,known,seed=i)
        if len(old):
            dx,dy=mem.dreams(np.where(known)[0],6000,100+i); st.practise(dx,dy,known,epochs=2,seed=100+i)
    print(ds,name,"bits",NB,"all-at-once %.4f  5 stages %.4f"%(aa,(st.predict(B,known)==yte).mean()),"%.0fs"%(time.time()-t0),flush=True)
