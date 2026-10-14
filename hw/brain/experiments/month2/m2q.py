"""few-shot with imagination: table practises on the k real examples plus imagined variants. usage: DS F"""
import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from sleep import SurpriseTable
import cochlea
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds,F=sys.argv[1],int(sys.argv[2])
z=np.load(f"{D}/sep_{ds}_F{F}_p2.npz"); ctr,cte=z["tr"],z["te"]
if ds=="speech": _,ytr,_,yte=cochlea.load_speech(D+"/speech",D+"/speech_pics_res.npz",cochlea.sound_picture_res)
else: _,ytr,_,yte=load(D,ds)
ytr=ytr.astype(int); yte=yte.astype(int); NB=ctr.shape[1]; allk=np.ones(10,bool)
def imagine(X,Y,mode,n_per,r):
    out=[];oy=[]
    for c in range(10):
        Xc=X[Y==c]; p=(Xc.sum(0)+0.5*X.mean(0))/(len(Xc)+0.5)          # class rate, nudged toward the overall rate
        for _ in range(n_per):
            if mode=="rate": d=r.random_sample(NB)<p
            elif mode=="jitter":
                x=Xc[r.randint(len(Xc))]; d=x&(r.random_sample(NB)<0.8)
            else:   # jitter + borrow: drop 20% of a real example's bits, add bits drawn from the class rate
                x=Xc[r.randint(len(Xc))]; d=(x&(r.random_sample(NB)<0.8))|(r.random_sample(NB)<p*0.2)
            out.append(d); oy.append(c)
    return np.array(out),np.array(oy)
for k in (1,5,20):
    res={}
    for mode in ("none","rate","jitter","both"):
        a=[]
        for s in range(3):
            r=np.random.RandomState(s); idx=np.concatenate([r.choice(np.where(ytr==c)[0],k,replace=False) for c in range(10)])
            X,Y=ctr[idx],ytr[idx]
            if mode!="none":
                dx,dy=imagine(X,Y,mode,200,r); X=np.concatenate([X,dx]); Y=np.concatenate([Y,dy])
            st=SurpriseTable(NB,10,cmax=15).practise(X,Y,allk,epochs=10,seed=s)
            a.append((st.predict(cte,allk)==yte).mean())
        res[mode]=round(float(np.mean(a)),4)
    print(ds,"k",k,res,flush=True)
