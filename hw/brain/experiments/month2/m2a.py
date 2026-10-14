"""ceiling check: (1) fast table at 4/5/8-bit counters, (2) concept cells pruned to S strongest synapses, 4-bit weights"""
import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from feature_layer import ConceptMemory
from sleep import SurpriseTable
import cochlea
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds=sys.argv[1]
if ds=="speech":
    z=np.load(D+"/codes_v2_speech_res_L8.npz"); _,ytr,_,yte=cochlea.load_speech(D+"/speech",D+"/speech_pics_res.npz",cochlea.sound_picture_res)
else:
    z=np.load(f"{D}/codes_v2_{ds}.npz"); _,ytr,_,yte=load(D,ds)
ctr,cte=z["tr"],z["te"]; ytr=ytr.astype(int); yte=yte.astype(int); NB=ctr.shape[1]; allk=np.ones(10,bool)
print(ds,"bits",NB,"active/example %.0f"%ctr.sum(1).mean(),flush=True)
for cm_ in (7,15,127):
    st=SurpriseTable(NB,10,cmax=cm_,margin=8).practise(ctr,ytr,allk)
    print(" table cmax",cm_,"acc %.4f"%(st.predict(cte)==yte).mean(),"KB %.0f"%(10*NB*np.ceil(np.log2(2*cm_+1))/8192),flush=True)
cm=ConceptMemory(NB,10,P=32).learn(ctr,ytr)
p=(cm.on+0.5)/(cm.n[...,None]+1.0)
for S in (64,128,256,512):
    # keep each cell's S most frequent bits; weight = 4-bit quantised frequency; score = sum of weights of active synapses
    idx=np.argsort(-p,axis=2)[:,:,:S]; w=np.round(np.take_along_axis(p,idx,2)*15).astype(np.int32)
    sc=[]
    for i in range(0,len(cte),1000):
        m=cte[i:i+1000][:,idx.reshape(-1)].reshape(-1,10,32,S)
        sc.append((m*w[None]).sum(-1).max(-1))
    acc=(np.concatenate(sc).argmax(1)==yte).mean()
    print(" sparse concept S",S,"acc %.4f"%acc,"KB %.0f"%(10*32*S*(np.ceil(np.log2(NB))+4)/8192),flush=True)
