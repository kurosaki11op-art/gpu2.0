import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import Cortex, load
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
for ds in ("mnist","fashion"):
  xtr,ytr,xte,yte=load(D,ds)
  for tb,ab,cp in [(16,10,4),(20,12,4),(24,12,8)]:
    t=time.time(); m=Cortex(784,10,tuple_bits=tb,addr_bits=ab,copies=cp); m.learn(xtr[:55000],ytr[:55000])
    va={b:(m.predict(xtr[55000:],b)==ytr[55000:]).mean() for b in (1,2,3,5,8,12,20)}
    b=max(va,key=va.get); print(ds,tb,ab,cp,"N",m.N,"KB",m.bytes()//1024,"b",b,"val %.4f test %.4f"%(va[b],(m.predict(xte,b)==yte).mean()),"%.0fs"%(time.time()-t),flush=True)
