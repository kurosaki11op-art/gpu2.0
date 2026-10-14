import sys,time,json; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
import cochlea
from feature_layer import Features, ConceptMemory
from sleep import SurpriseTable
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
F=int(sys.argv[1]); pool=int(sys.argv[2]); src_mode=sys.argv[3]; chans=json.loads(sys.argv[4]); chans=[tuple(c) if isinstance(c,list) else c for c in chans]
xtr,ytr,xte,yte=cochlea.load_speech(D+"/speech",D+"/speech_pics_res.npz",cochlea.sound_picture_res); ytr=ytr.astype(int); yte=yte.astype(int)
src=xtr[np.isin(ytr,(0,1))][:12000] if src_mode=="stage1" else xtr[np.random.RandomState(0).choice(len(xtr),12000,replace=False)]
t0=time.time(); fes=[Features(F,thr=c,pool=pool).fit(src) for c in chans]
enc=lambda x: np.concatenate([np.concatenate([f.encode(x[i:i+5000]) for f in fes],1) for i in range(0,len(x),5000)])
ctr,cte=enc(xtr),enc(xte); NB=ctr.shape[1]
st=SurpriseTable(NB,10).practise(ctr,ytr,np.ones(10,bool)); cm=ConceptMemory(NB,10,P=32).learn(ctr,ytr)
print("F",F,"pool",pool,src_mode,chans,"bits",NB,"table %.4f concept %.4f"%((st.predict(cte)==yte).mean(),(cm.predict(cte)==yte).mean()),"%.0fs"%(time.time()-t0),flush=True)
