import os,sys,json,time
sys.path.insert(0,"new_start/experiments/k1")
os.environ["K1_DATA"]="D:/cortex_data"; os.environ["K1_CACHE"]="k1_codes.npz"
import numpy as np, torch, torch.nn.functional as F
import k1_data_efficiency as k1
from cortex_slow import CortexSlow
xtr,ytr,xte,yte=k1.load(k1.D,"fashion"); ytr=ytr.astype(np.int64); yte=yte.astype(np.int64)
t=time.time(); ctr,cte=k1.codes(xtr,ytr,xte); print("codes",ctr.shape,round(time.time()-t),"s",flush=True)
na=float(ctr[:5000].sum(1).mean()); ex=26*na*k1.E_ADD; enc=k1.ENC_BITOPS*k1.E_BIT; fit=12000*2*enc
for s in (1,2,3):
    t=time.time(); m=CortexSlow(ctr.shape[1],ch=500,K=5,night_stop=2,daydream=1,seed=s); m.stage(ctr,ytr); S=m.S.T.astype(np.int32)
    print("L seed",s,"acc",float(((cte.astype(np.int32)@S).argmax(1)==yte).mean()),round(time.time()-t),"s",flush=True)
eL=(fit+60000*(enc+ex))*1e-12; print("eL raw J",eL,"x28",eL*28,flush=True)
X=torch.tensor(xtr.reshape(-1,1,28,28)/255.,dtype=torch.float32);Y=torch.tensor(ytr);Xt=torch.tensor(xte.reshape(-1,1,28,28)/255.,dtype=torch.float32);Yt=torch.tensor(yte)
for s in range(3):
    torch.manual_seed(s);g=np.random.RandomState(s);net=k1.Net();opt=torch.optim.Adam(net.parameters(),1e-3);accs=[]
    for ep in range(15):
        o=g.permutation(60000)
        for i in range(0,60000,64):
            b=o[i:i+64];opt.zero_grad();F.cross_entropy(net(X[b]),Y[b]).backward();opt.step()
        with torch.no_grad(): accs.append(round(float((net(Xt).argmax(1)==Yt).float().mean()),4))
    print("cnn seed",s,accs,flush=True)
print("J per epoch at 1.5pJ, 3x fwd",60000*3*k1.CNN_FWD_MAC*1.5e-12)
