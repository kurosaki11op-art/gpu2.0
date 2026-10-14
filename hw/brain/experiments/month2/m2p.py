"""consolidation (old-class rows less plastic) and sharper dreams, with 10-bit scaled counts. usage: DS F"""
import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from rate_memory import ScaledCounts
import cochlea
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds,F=sys.argv[1],int(sys.argv[2])
z=np.load(f"{D}/sep_{ds}_F{F}_p2.npz"); ctr,cte=z["tr"],z["te"]
if ds=="speech": _,ytr,_,yte=cochlea.load_speech(D+"/speech",D+"/speech_pics_res.npz",cochlea.sound_picture_res)
else: _,ytr,_,yte=load(D,ds)
ytr=ytr.astype(int); yte=yte.astype(int); NB=ctr.shape[1]
stages=[(0,1),(2,3),(4,5),(6,7),(8,9)]
def practise(W,code,y,known,plast,epochs,seed,cmax=15,margin=8):
    r=np.random.RandomState(seed)
    for _ in range(epochs):
        o=r.permutation(len(y))
        for i in range(0,len(y),50):
            idx=o[i:i+50]; c=code[idx].astype(np.int32); yy=y[idx]; ar=np.arange(len(idx))
            s=c@W.T; s[:,~known]=-(1<<30); t=s[ar,yy].copy(); s[ar,yy]=-(1<<30); rv=s.argmax(1)
            sup=(t-s[ar,rv])<=margin
            # plasticity per class row: an update to row k is applied with probability plast[k]
            okp=r.random_sample(len(idx))<plast[yy]; okr=r.random_sample(len(idx))<plast[rv]
            a=sup&okp; b=sup&okr
            np.add.at(W,yy[a],c[a]); np.subtract.at(W,rv[b],c[b]); np.clip(W,-cmax,cmax,out=W)
def dreams(mem,classes,n,seed,sharp):
    g=np.random.RandomState(seed); X=[];Y=[]
    for c in classes:
        p=(mem.on[c]+0.5)/(mem.n[c]+1.0)
        if sharp: p=p**sharp/(p**sharp+(1-p)**sharp)
        X.append(g.random_sample((n,NB))<p); Y.append(np.full(n,c))
    return np.concatenate(X),np.concatenate(Y)
def run(old_p,sharp,night,nd=6000):
    t0=time.time(); W=np.zeros((10,NB),np.int32); known=np.zeros(10,bool); res=[]; mem=ScaledCounts(NB,10,B=10)
    for i,s in enumerate(stages):
        sel=np.isin(ytr,s); mem.learn(ctr[sel],ytr[sel]); old=np.where(known)[0]; known[list(s)]=True
        plast=np.ones(10); plast[old]=old_p
        X,Y=ctr[sel],ytr[sel]
        if len(old):
            dx,dy=dreams(mem,old,nd,i,sharp); X=np.concatenate([X,dx]); Y=np.concatenate([Y,dy])
        practise(W,X,Y,known,plast,3,i)
        if night and len(old):
            dx,dy=dreams(mem,np.where(known)[0],nd,100+i,sharp); practise(W,dx,dy,known,np.ones(10),2,100+i)
        seen=np.isin(yte,np.where(known)[0]); sc=cte[seen].astype(np.int32)@W.T; sc[:,~known]=-(1<<30)
        res.append((sc.argmax(1)==yte[seen]).mean())
    print(ds,"old plasticity",old_p,"sharp",sharp,"night",night,np.round(res,4),"%.0fs"%(time.time()-t0),flush=True)
run(1.0,0,1)          # reference = test o (10-bit)
run(0.25,0,1)
run(1.0,1.5,1)
run(0.25,1.5,1)
run(0.25,0,0)
