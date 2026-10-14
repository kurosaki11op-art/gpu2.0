"""stages with dreams; decision = fast table only (5-bit). dream source = counts | concept P at b bits. usage: DS F"""
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
    r=np.random.RandomState(seed); X=[];Y=[]
    lv=np.geomspace(1/256,0.98,2**b)
    for c in classes:
        p=(cm.on[c]+0.5)/(cm.n[c][:,None]+1.0); q=lv[np.abs(np.log(p)[...,None]-np.log(lv)).argmin(-1)]
        cell=r.choice(cm.P,n,p=cm.n[c]/cm.n[c].sum())
        X.append(r.random_sample((n,NB))<q[cell]); Y.append(np.full(n,c))
    return np.concatenate(X),np.concatenate(Y)
def run(src,P=8,b=3,cmax=15,nd=6000):
    t0=time.time(); st=SurpriseTable(NB,10,cmax=cmax); known=np.zeros(10,bool); res=[]
    mem=CountMemory(NB,10) if src=="count" else ConceptMemory(NB,10,P=P)
    for i,s in enumerate(stages):
        sel=np.isin(ytr,s); mem.learn(ctr[sel],ytr[sel]); old=np.where(known)[0]; known[list(s)]=True
        X,Y=ctr[sel],ytr[sel]
        if len(old):
            dx,dy=count_dreams(mem,old,nd,seed=i) if src=="count" else qdreams(mem,old,nd,b,i)
            X=np.concatenate([X,dx]); Y=np.concatenate([Y,dy])
        st.practise(X,Y,known,seed=i)
        seen=np.isin(yte,np.where(known)[0]); res.append((st.predict(cte[seen],known)==yte[seen]).mean())
    kb=10*NB*8/8192 if src=="count" else 10*P*NB*b/8192
    print(ds,src,"P",P,"bits",b,"dream-mem KB %.0f"%kb,"table KB %.0f"%(10*NB*5/8192),np.round(res,4),"%.0fs"%(time.time()-t0),flush=True)
run("count")
for P,b in [(4,3),(8,3),(8,2),(16,2)]:
    run("concept",P,b)
