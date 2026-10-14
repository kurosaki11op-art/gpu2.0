import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import Cortex, load
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
xtr,ytr,xte,yte=load(D,sys.argv[1])
for tb,ab,cp,cm,ep,bs,mg in [(12,8,2,7,3,50,None),(12,8,2,7,3,50,0),(16,8,2,7,3,50,None),(16,8,2,7,6,50,None),(16,8,2,15,3,50,None),(20,8,2,7,3,50,None),(16,7,2,7,3,50,None)]:
    t=time.time(); m=Cortex(784,10,tuple_bits=tb,addr_bits=ab,copies=cp,cmax=cm)
    accs=[]
    for e in range(ep):
        m.learn_surprise(xtr[:55000],ytr[:55000],epochs=1,bs=bs,margin=mg,seed=e); accs.append((m.scores(xtr[55000:]).argmax(1)==ytr[55000:]).mean())
    te=(m.scores(xte).argmax(1)==yte).mean()
    print(sys.argv[1],(tb,ab,cp,cm,ep,bs,mg),"KB %.0f"%(m.bits()/8192),"val/epoch",np.round(accs,4),"test %.4f"%te,"writes",m.last_writes,"%.0fs"%(time.time()-t),flush=True)
