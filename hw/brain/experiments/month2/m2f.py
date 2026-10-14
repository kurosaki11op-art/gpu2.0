"""accuracy vs code size. usage: m2c.py DS F POOL FOLD   (FOLD=0: no folding; else fold the code into FOLD bits)"""
import sys,time,os; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from feature_layer import Features, ConceptMemory
from sleep import SurpriseTable
import cochlea
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds,F,pool,fold=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]),int(sys.argv[4])
if ds=="speech":
    xtr,ytr,xte,yte=cochlea.load_speech(D+"/speech",D+"/speech_pics_res.npz",cochlea.sound_picture_res)
    CH=(20,50,80,110,140,170,200,230,("on",8),("off",8)); base=f"{D}/codes_v2_speech_res_L8.npz"
else:
    xtr,ytr,xte,yte=load(D,ds); CH=(50,150,("on",8),("off",8)); base=f"{D}/codes_v2_{ds}.npz"
ytr=ytr.astype(int); yte=yte.astype(int); t0=time.time()
if F==128 and pool==2:
    z=np.load(base); ctr,cte=z["tr"],z["te"]
else:
    src=xtr[np.isin(ytr,(0,1))][:12000]
    fes=[Features(F,thr=list(CH),pool=pool).fit(src)] if os.environ.get("JOINT") else [Features(F,thr=c,pool=pool).fit(src) for c in CH]
    enc=lambda x: np.concatenate([np.concatenate([f.encode(x[i:i+5000]) for f in fes],1) for i in range(0,len(x),5000)])
    ctr,cte=enc(xtr),enc(xte)
if fold:
    wire=np.random.RandomState(1).randint(0,fold,ctr.shape[1])        # each input bit wired to one of FOLD neurons (OR)
    f_=lambda c: np.stack([np.bincount(wire[np.nonzero(r)[0]],minlength=fold)>0 for r in c])
    ctr,cte=np.concatenate([f_(ctr[i:i+5000]) for i in range(0,len(ctr),5000)]),f_(cte)
NB=ctr.shape[1]; allk=np.ones(10,bool)
out=[]
for cm_ in (127,15):
    out.append("table%d %.4f"%(cm_,(SurpriseTable(NB,10,cmax=cm_).practise(ctr,ytr,allk).predict(cte)==yte).mean()))
np.savez_compressed(f"{D}/sep_{ds}_F{F}_p{pool}.npz",tr=ctr,te=cte)
for P in (16,8):
    cm=ConceptMemory(NB,10,P=P).learn(ctr,ytr); out.append("concept%d %.4f"%(P,(cm.predict(cte)==yte).mean()))
    # synapse precision: store each (cell, bit) firing rate as a b-bit level on a log scale (2^b levels from 1/256 to 1)
    p=(cm.on+0.5)/(cm.n[...,None]+1.0)
    for b in (4,3,2):
        L=2**b; lv=np.geomspace(1/256,0.98,L); q=lv[np.abs(np.log(p)[...,None]-np.log(lv)).argmin(-1)]
        d=(np.log(q)-np.log1p(-q)).astype(np.float32); c0=np.log1p(-q).sum(-1)
        sc=np.concatenate([(cte[i:i+2000].astype(np.float32)@d.reshape(-1,NB).T).reshape(-1,10,P)+c0 for i in range(0,len(cte),2000)]).max(2)
        out.append("c%d@%dbit %.4f(%.0fKB)"%(P,b,(sc.argmax(1)==yte).mean(),10*P*NB*b/8192))
print(ds,"F",F,"pool",pool,"fold",fold,"bits",NB,"active %.0f"%ctr.sum(1).mean()," ".join(out),"%.0fs"%(time.time()-t0),flush=True)
