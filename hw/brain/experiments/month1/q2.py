import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import Cortex, load
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
xtr,ytr,xte,yte=load(D,sys.argv[1])
for tb,ab,cp,k,cm,loc in [(16,8,2,2,15,0),(16,8,2,2,15,4),(12,8,2,2,15,3),(16,8,4,2,15,4),(16,7,4,2,7,4),(20,9,4,2,15,5),(12,6,4,1,7,3)]:
    t=time.time(); m=Cortex(784,10,tuple_bits=tb,addr_bits=ab,copies=cp,hashes=k,cmax=cm,local=loc); m.learn(xtr[:55000],ytr[:55000])
    va={b:(m.predict(xtr[55000:],b)==ytr[55000:]).mean() for b in range(1,cm+1)}
    b=max(va,key=va.get); print(sys.argv[1],(tb,ab,cp,k,cm,loc),"N",m.N,"KB %.0f"%(m.bits()/8192),"b",b,"val %.4f test %.4f"%(va[b],(m.predict(xte,b)==yte).mean()),"%.0fs"%(time.time()-t),flush=True)
