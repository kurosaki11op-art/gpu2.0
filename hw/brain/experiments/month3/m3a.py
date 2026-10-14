"""split dream memory: per class, counts kept separately for each on/off pattern of m split bits (the class's most
50/50 bits among its first 100 examples). Dreams pick a pattern by its count, then draw bits from that bin. Float sim,
day + night2 schedule as m2i (table 5-bit). usage: DS F"""
import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from sleep import SurpriseTable
import cochlea
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds,F=sys.argv[1],int(sys.argv[2])
z=np.load(f"{D}/sep_{ds}_F{F}_p2.npz"); ctr,cte=z["tr"],z["te"]
if ds=="speech": _,ytr,_,yte=cochlea.load_speech(D+"/speech",D+"/speech_pics_res.npz",cochlea.sound_picture_res)
else: _,ytr,_,yte=load(D,ds)
ytr=ytr.astype(int); yte=yte.astype(int); NB=ctr.shape[1]
stages=[(0,1),(2,3),(4,5),(6,7),(8,9)]
class Split:
    def __init__(s,m,top=1023):
        s.m=m; s.K=2**m; s.on=np.zeros((10,s.K,NB),np.int64); s.n=np.zeros((10,s.K),np.int64); s.bits={}; s.top=top
    def cell(s,c,X):
        b=s.bits[c]; idx=np.zeros(len(X),int)
        for j,bb in enumerate(b): idx|=X[:,bb].astype(int)<<j
        return idx
    def learn(s,X,y):
        for c in np.unique(y):
            Xc=X[y==c]
            if c not in s.bits:
                p=Xc[:100].mean(0); s.bits[c]=list(np.argsort(np.abs(p-0.5))[:s.m])
            cl=s.cell(c,Xc)
            for k in range(s.K):
                s.on[c,k]+=Xc[cl==k].sum(0); s.n[c,k]+=(cl==k).sum()
                while s.n[c,k]>=s.top: s.on[c,k]>>=1; s.n[c,k]>>=1
    def dreams(s,classes,n,seed):
        g=np.random.RandomState(seed); X=[];Y=[]
        for c in classes:
            w=(s.n[c]+1e-9)/(s.n[c]+1e-9).sum(); k=g.choice(s.K,n,p=w)
            p=(s.on[c]+0.5)/(s.n[c][:,None]+1.0)
            X.append(g.random_sample((n,NB))<p[k]); Y.append(np.full(n,c))
        return np.concatenate(X),np.concatenate(Y)
def run(m,nd=6000):
    t0=time.time(); st=SurpriseTable(NB,10,cmax=15); known=np.zeros(10,bool); res=[]; mem=Split(m)
    for i,s in enumerate(stages):
        sel=np.isin(ytr,s); mem.learn(ctr[sel],ytr[sel]); old=np.where(known)[0]; known[list(s)]=True
        X,Y=ctr[sel],ytr[sel]
        if len(old):
            dx,dy=mem.dreams(old,nd,i); X=np.concatenate([X,dx]); Y=np.concatenate([Y,dy])
        st.practise(X,Y,known,seed=i)
        if len(old):
            dx,dy=mem.dreams(np.where(known)[0],nd,100+i); st.practise(dx,dy,known,epochs=2,seed=100+i)
        seen=np.isin(yte,np.where(known)[0]); res.append((st.predict(cte[seen],known)==yte[seen]).mean())
    print(ds,"split bits",m,"memory x",2**m,np.round(res,4),"%.0fs"%(time.time()-t0),flush=True)
for m in (0,1,2,3):
    run(m)
