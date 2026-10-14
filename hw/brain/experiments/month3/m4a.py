"""second sensory layer (V2): competitive detectors on 2x2-cell windows of the first-layer code map (6x6 cells x 128
features per channel group), learned without labels; code = V1 code + V2 code. Float sim, fast table (5-bit) all at
once + 5 stages with count dreams (as month 2). usage: DS F2"""
import sys,time; sys.path.insert(0,"/home/user/gpu2.0/hw/brain"); import numpy as np
from cortex_core import load
from sleep import SurpriseTable
from rate_memory import ScaledCounts
D="/tmp/claude-0/-home-user-gpu2-0/6c8eff4e-7965-54eb-adef-d1487ac4cfac/scratchpad/data"
ds,F2=sys.argv[1],int(sys.argv[2])
z=np.load(f"{D}/sep_{ds}_F32_p2.npz"); ctr,cte=z["tr"],z["te"]
_,ytr,_,yte=load(D,ds); ytr=ytr.astype(int); yte=yte.astype(int)
def cells(code):   # (B,4608) -> (B,6,6,128): 4 channel groups x 32 features per cell
    return code.reshape(len(code),4,6,6,32).transpose(0,2,3,1,4).reshape(len(code),6,6,128)
def windows(m):    # 2x2-cell windows at stride 1 -> (B,25,512)
    return np.stack([m[:,i:i+2,j:j+2,:].reshape(len(m),-1) for i in range(5) for j in range(5)],1)
class V2:
    def __init__(s,F,seed=0): s.F=F; s.r=np.random.RandomState(seed)
    def fit(s,code,passes=3,cmax=31):
        p=windows(cells(code)).reshape(-1,512); p=p[p.sum(1)>=4]; p=p[s.r.choice(len(p),min(200000,len(p)),replace=False)]
        s.cnt=np.where(p[s.r.choice(len(p),s.F)],1,-1).astype(np.int32)
        for _ in range(passes):
            wins=np.zeros(s.F,int)
            for i in range(0,len(p),1000):
                b=p[i:i+1000]; w=s.win(b); np.add.at(s.cnt,w,np.where(b,1,-1)); np.clip(s.cnt,-cmax,cmax,out=s.cnt); wins+=np.bincount(w,minlength=s.F)
            dead=np.where(wins==0)[0]; s.cnt[dead]=np.where(p[s.r.choice(len(p),len(dead))],1,-1)
        return s
    def win(s,b):
        t=(s.cnt>=0); return (b.astype(np.int16)@t.T.astype(np.int16)*2-b.sum(1,keepdims=True)-t.sum(1)[None]).argmax(1)  # agreements on active bits
    def encode(s,code):
        w=windows(cells(code)); B=len(code); flat=w.reshape(-1,512); win=s.win(flat).reshape(B,25); on=(w.sum(2)>=4)
        out=np.zeros((B,25,s.F),bool); bi,pi=np.nonzero(on); out[bi,pi,win[bi,pi]]=True
        return out.reshape(B,-1)
t0=time.time()
v2=V2(F2).fit(ctr[np.isin(ytr,(0,1))][:12000])
e2=lambda c: np.concatenate([v2.encode(c[i:i+5000]) for i in range(0,len(c),5000)])
c2tr,c2te=e2(ctr),e2(cte)
for name,(A,B) in {"V1":(ctr,cte),"V1+V2":(np.concatenate([ctr,c2tr],1),np.concatenate([cte,c2te],1))}.items():
    NB=A.shape[1]; allk=np.ones(10,bool)
    aa=(SurpriseTable(NB,10,cmax=15).practise(A,ytr,allk).predict(B,allk)==yte).mean()
    st=SurpriseTable(NB,10,cmax=15); mem=ScaledCounts(NB,10,B=10); known=np.zeros(10,bool)
    for i,s in enumerate([(0,1),(2,3),(4,5),(6,7),(8,9)]):
        sel=np.isin(ytr,s); mem.learn(A[sel],ytr[sel]); old=np.where(known)[0]; known[list(s)]=True; X,Y=A[sel],ytr[sel]
        if len(old):
            dx,dy=mem.dreams(old,6000,i); X=np.concatenate([X,dx]); Y=np.concatenate([Y,dy])
        st.practise(X,Y,known,seed=i)
        if len(old):
            dx,dy=mem.dreams(np.where(known)[0],6000,100+i); st.practise(dx,dy,known,epochs=2,seed=100+i)
    stg=(st.predict(B,known)==yte).mean()
    print(ds,"F2",F2,name,"bits",NB,"all-at-once %.4f  5 stages %.4f"%(aa,stg),"%.0fs"%(time.time()-t0),flush=True)
