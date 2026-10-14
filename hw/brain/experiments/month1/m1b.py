import sys,time,json; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from feature_layer import Features, CountMemory
from sleep import SurpriseTable
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds=sys.argv[1]; F=int(sys.argv[2]); pool=int(sys.argv[3]); chans=json.loads(sys.argv[4])
chans=[tuple(c) if isinstance(c,list) else c for c in chans]
xtr,ytr,xte,yte=load(D,ds); ytr=ytr.astype(int); yte=yte.astype(int)
t0=time.time(); src=xtr[np.isin(ytr,(0,1))][:12000]
fes=[Features(F,thr=c,pool=pool).fit(src) for c in chans]
enc=lambda x: np.concatenate([np.concatenate([f.encode(x[i:i+5000]) for f in fes],1) for i in range(0,len(x),5000)])
ctr,cte=enc(xtr),enc(xte); NB=ctr.shape[1]
cm=CountMemory(NB,10).learn(ctr,ytr); st=SurpriseTable(NB,10).practise(ctr,ytr,np.ones(10,bool))
print(ds,"F",F,"pool",pool,chans,"bits",NB,"count %.4f table %.4f"%((cm.predict(cte)==yte).mean(),(st.predict(cte)==yte).mean()),"%.0fs"%(time.time()-t0),flush=True)
