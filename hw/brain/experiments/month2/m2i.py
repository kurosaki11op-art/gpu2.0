"""better sleep, fast table = only decision maker. dream source = count memory (8-bit) or concept P8@3bit.
night modes: day   = practise on new real + dreams of old classes (as in m2h)
             night = day, then a night of dreams of ALL known classes (new included)
             night2= day, then night with 2x dreams and 2 passes
usage: DS F"""
import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from feature_layer import ConceptMemory, CountMemory
from sleep import SurpriseTable, dreams as count_dreams
import cochlea
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds,F=sys.argv[1],int(sys.argv[2])
z=np.load(f"{D}/sep_{ds}_F{F}_p2.npz"); ctr,cte=z["tr"],z["te"]
if ds=="speech": _,ytr,_,yte=cochlea.load_speech(D+"/speech",D+"/speech_pics_res.npz",cochlea.sound_picture_res)
else: _,ytr,_,yte=load(D,ds)
ytr=ytr.astype(int); yte=yte.astype(int); NB=ctr.shape[1]
stages=[(0,1),(2,3),(4,5),(6,7),(8,9)]
def qdreams(cm,classes,n,b,seed):
    r=np.random.RandomState(seed); X=[];Y=[]; lv=np.geomspace(1/256,0.98,2**b)
    for c in classes:
        p=(cm.on[c]+0.5)/(cm.n[c][:,None]+1.0); q=lv[np.abs(np.log(p)[...,None]-np.log(lv)).argmin(-1)]
        cell=r.choice(cm.P,n,p=cm.n[c]/cm.n[c].sum()); X.append(r.random_sample((n,NB))<q[cell]); Y.append(np.full(n,c))
    return np.concatenate(X),np.concatenate(Y)
def run(src,night,nd=6000):
    t0=time.time(); st=SurpriseTable(NB,10,cmax=15); known=np.zeros(10,bool); res=[]
    mem=CountMemory(NB,10) if src=="count" else ConceptMemory(NB,10,P=8)
    dr=(lambda cl,n,s: count_dreams(mem,cl,n,seed=s)) if src=="count" else (lambda cl,n,s: qdreams(mem,cl,n,3,s))
    for i,s in enumerate(stages):
        sel=np.isin(ytr,s); mem.learn(ctr[sel],ytr[sel]); old=np.where(known)[0]; known[list(s)]=True
        X,Y=ctr[sel],ytr[sel]
        if len(old):
            dx,dy=dr(old,nd,i); X=np.concatenate([X,dx]); Y=np.concatenate([Y,dy])
        st.practise(X,Y,known,seed=i)
        if night!="day" and i>0:
            mult=2 if night=="night2" else 1
            dx,dy=dr(np.where(known)[0],nd*mult//2,100+i)
            st.practise(dx,dy,known,epochs=mult,seed=100+i)
        seen=np.isin(yte,np.where(known)[0]); res.append((st.predict(cte[seen],known)==yte[seen]).mean())
    print(ds,src,night,np.round(res,4),"%.0fs"%(time.time()-t0),flush=True)
for src in ("count","concept"):
    for night in ("night","night2"):
        run(src,night)
