"""joint sparse codes (+k-WTA, +fold) -> table, full concept cells, sparse-exact concept cells. usage: DS F K FOLD"""
import sys,time,os; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from feature_layer import Features, ConceptMemory
from sleep import SurpriseTable
import cochlea
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds,F,K,fold=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])
if ds=="speech":
    xtr,ytr,xte,yte=cochlea.load_speech(D+"/speech",D+"/speech_pics_res.npz",cochlea.sound_picture_res)
    CH=[20,50,80,110,140,170,200,230,("on",8),("off",8)]
else:
    xtr,ytr,xte,yte=load(D,ds); CH=[50,150,("on",8),("off",8)]
ytr=ytr.astype(int); yte=yte.astype(int); t0=time.time()
cache=f"{D}/joint_{ds}_F{F}_k{K}.npz"
if os.path.exists(cache):
    z=np.load(cache); ctr,cte=z["tr"],z["te"]
else:
    fe=Features(F,thr=CH,k=K).fit(xtr[np.isin(ytr,(0,1))][:12000])
    ctr=np.concatenate([fe.encode(xtr[i:i+3000]) for i in range(0,len(xtr),3000)]); cte=np.concatenate([fe.encode(xte[i:i+3000]) for i in range(0,len(xte),3000)])
    np.savez_compressed(cache,tr=ctr,te=cte)
if fold:
    wire=np.random.RandomState(1).randint(0,fold,ctr.shape[1])
    f_=lambda c: np.stack([np.bincount(wire[np.nonzero(r)[0]],minlength=fold)>0 for r in c])
    ctr,cte=f_(ctr),f_(cte)
NB=ctr.shape[1]; allk=np.ones(10,bool); out=[]
for cm_ in (127,15):
    out.append("table%d %.4f"%(cm_,(SurpriseTable(NB,10,cmax=cm_).practise(ctr,ytr,allk).predict(cte)==yte).mean()))
for P in (32,16):
    cm=ConceptMemory(NB,10,P=P).learn(ctr,ytr); out.append("concept%d %.4f"%(P,(cm.predict(cte)==yte).mean()))
    # sparse-exact: a cell stores only bits with on-count >= 2; all other bits use a floor rate eps
    for eps_n in (1,):
        p=(cm.on+0.5)/(cm.n[...,None]+1.0); stored=cm.on>=2
        eps=0.5/(cm.n[...,None]+1.0)
        pe=np.where(stored,p,eps)
        lg=lambda v: np.log(v)-np.log1p(-v)
        w=np.where(stored,lg(pe)-lg(eps),0).astype(np.float32)               # weight only on stored synapses
        const=np.log1p(-pe).sum(-1)                                          # per-cell constant
        # quantise weights to 4 bits per cell
        mx=np.abs(w).max(-1,keepdims=True)+1e-9; wq=np.round(w/mx*7)*mx/7
        sc=np.concatenate([(cte[i:i+2000].astype(np.float32)@wq.reshape(-1,NB).T).reshape(-1,10,P)+const for i in range(0,len(cte),2000)]).max(2)
        nsyn=stored.sum(-1)
        out.append("sparse%d %.4f syn/cell %.0f KB %.0f"%(P,(sc.argmax(1)==yte).mean(),nsyn.mean(),nsyn.sum()*(np.ceil(np.log2(NB))+4)/8192))
print(ds,"joint F",F,"k",K,"fold",fold,"bits",NB,"active %.0f"%ctr.sum(1).mean()," ".join(out),"%.0fs"%(time.time()-t0),flush=True)
