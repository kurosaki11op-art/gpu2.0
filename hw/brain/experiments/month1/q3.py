import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import Cortex, load
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
xtr,ytr,xte,yte=load(D,sys.argv[1])
for tb,ab,cp,cm,loc,ep in [(12,8,2,7,0,3),(12,8,2,7,3,3),(16,8,2,7,0,3),(8,8,2,7,0,3),(12,6,2,7,0,3),(12,8,4,7,0,3),(12,8,2,7,0,6)]:
    t=time.time(); m=Cortex(784,10,tuple_bits=tb,addr_bits=ab,copies=cp,cmax=cm,local=loc)
    m.learn_surprise(xtr[:55000],ytr[:55000],epochs=ep)
    v=(m.scores(xtr[55000:]).argmax(1)==ytr[55000:]).mean(); te=(m.scores(xte).argmax(1)==yte).mean()
    print(sys.argv[1],(tb,ab,cp,cm,loc,ep),"N",m.N,"KB %.0f"%(m.bits()/8192),"val %.4f test %.4f"%(v,te),"writes last epoch",m.last_writes,"%.0fs"%(time.time()-t),flush=True)
