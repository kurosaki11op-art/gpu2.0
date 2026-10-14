import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import Cortex, load
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
xtr,ytr,xte,yte=load(D,"mnist"); ytr=ytr.astype(int); yte=yte.astype(int)
def best_b(m,x,y,bs=range(1,16)):
    v={b:(m.predict(x,b)==y).mean() for b in bs}; return max(v,key=v.get)
for cfg in [dict(tuple_bits=16,addr_bits=8,copies=2,cmax=15,hashes=2),dict(tuple_bits=20,addr_bits=10,copies=4,cmax=15,hashes=2)]:
  m=Cortex(784,10,**cfg); m.learn(xtr[:55000],ytr[:55000]); b=best_b(m,xtr[55000:],ytr[55000:])
  print(cfg,"KB %.0f"%(m.bits()/8192),"full b",b,(m.predict(xte,b)==yte).mean(),flush=True)
  for k in (1,5,20):
    a=[]
    for s in range(3):
      r=np.random.RandomState(s); idx=np.concatenate([r.choice(np.where(ytr==c)[0],k,replace=False) for c in range(10)])
      mm=Cortex(784,10,**cfg); mm.learn(xtr[idx],ytr[idx]); a.append((mm.predict(xte,1)==yte).mean())
    print(" few-shot",k,np.mean(a),flush=True)
