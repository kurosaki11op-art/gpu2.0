"""Class-specific detector dictionary (24 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed). Failure studied: moving shared detector templates by blame (blame_detectors.py) gave no reliable gain.
New mechanism: use the labels only to decide WHICH detectors exist: each class gets its own detectors fitted (the same unsupervised Hebbian rule) on that class's patches, then all detectors compete (hard winner) at encoding as usual.
Compared at EQUAL detector count (80 per channel, code 11,520 bits): (a) unsupervised dictionary fitted on the same number of random images; (b) class-specific dictionary (8 per class per channel). Table trained on 30,000 training images, tested on all 10,000. Win-win test: accuracy, cluster accuracy and Shirt AP all up, nothing else down."""
import sys, os, time, numpy as np
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features
from cortex_core import load
from cortex_slow import CortexSlow
D, DS = sys.argv[1], sys.argv[2]; xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); NTR = 30000; PER = int(os.environ.get("PER", 8)); CL = np.array([0, 2, 4, 6])
CH = (50, 150, ("on", 8), ("off", 8)); sub = np.arange(NTR); t0 = time.time()
def enc(fl, x): return np.concatenate([np.concatenate([g.encode(x[i:i + 200]) for g in fl], 1) for i in range(0, len(x), 200)])
def evaluate(tag, fl):
    ctr, cte = enc(fl, xtr[sub]), enc(fl, xte); m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(NTR); m.stage(ctr[sel], ytr[sub][sel]); S = m.S.astype(np.int32)
    sc = cte.astype(np.int32) @ S.T; p = sc.argmax(1); mk = np.isin(yte, CL); cl = (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("%-46s bits %6d | accuracy %.4f | cluster %.4f | Shirt recall %.3f T-shirt %.3f Pullover %.3f Coat %.3f | Shirt AP %.3f | %.0fs" % (tag, ctr.shape[1], (p == yte).mean(), cl, (p[yte == 6] == 6).mean(), (p[yte == 0] == 0).mean(), (p[yte == 2] == 2).mean(), (p[yte == 4] == 4).mean(), ap, time.time() - t0), flush=True)
rs = np.random.RandomState(7)
fl_unsup = [Features(PER * 10, thr=c, pool=4).fit(xtr[sub][rs.choice(NTR, 12000, replace=False)]) for c in CH]; evaluate("unsupervised dictionary, %d per channel" % (PER * 10), fl_unsup)
fl_cls = []
for c in CH:
    f = Features(PER * 10, thr=c, pool=4); cnts = []
    for k in range(10):
        fk = Features(PER, thr=c, pool=4, seed=k).fit(xtr[sub][ytr[sub] == k][:2500]); cnts.append(fk.cnt)
    f.cnt = np.concatenate(cnts, 0); fl_cls.append(f)
evaluate("class-specific dictionary, %d x 10 classes" % PER, fl_cls)
