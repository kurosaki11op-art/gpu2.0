"""Embedding-space prototypes for new words, with several prototypes for the well-known old words (20 Oct): the old SC words have thousands of clips, so each is modelled by KOLD prototypes (integer competitive learning in the embedding space: winner = smallest L1 distance, winner += (x - winner) >> 5) instead of one mean; a new word from k recordings is modelled by its MEAN or by each recording as its own exemplar. Table trained on the 5 old words
+ 10 FSDD digits (no rows for new words), embedding = integer scores over the 15 known classes. 3 draws, single view, all ten / new / old. SIMULATED. usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
D = sys.argv[1]
c = np.load(os.path.join(D, "word_codes_shipped.npz")); ctr, cte, cfs, yfs = c["tr"], c["te"], c["fs"], c["yfs"].astype(int) + 10
f = np.load(os.path.join(D, "speech_framesums_int.npz")); y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int)
old = np.where(ytr < 5)[0]; g0 = np.random.RandomState(0)
m = CortexInt(ctr.shape[1], n_cls=20, seed=1, night=0, daydream=0)
A = np.concatenate([ctr[old], cfs]); Y = np.concatenate([ytr[old], yfs]); pp = g0.permutation(len(Y)); m.stage(A[pp], Y[pp])
keep = list(range(5)) + list(range(10, 20)); W = m.W[keep].astype(np.int32)
ztr = (ctr.astype(np.int32) @ W.T).astype(np.float32); zte = (cte.astype(np.int32) @ W.T).astype(np.float32)


def ema_protos(X, K, shift=5, seed=0):
    """integer competitive learning: K prototypes per class, winner = smallest L1 distance, winner += (x - winner) >> shift (shifts and adds only); first K examples seed the prototypes"""
    r = np.random.RandomState(seed); X = X[r.permutation(len(X))]; C = X[:K].astype(np.int64).copy(); Xi = X.astype(np.int64)
    for i in range(K, len(Xi)):
        j = np.abs(C - Xi[i]).sum(1).argmin(); C[j] += (Xi[i] - C[j]) >> shift
    return C.astype(np.float32)


for KOLD in (1, 2, 3, 4, 6):
    oldp = [ema_protos(ztr[ytr == cl], KOLD) if KOLD > 1 else ztr[ytr == cl].mean(0, keepdims=True) for cl in range(5)]
    for newmode in ("mean",):
        for k in (1, 2, 5):
            rows = []
            for s in (1, 2, 3):
                g = np.random.RandomState(1000 * s); idx = {cl: g.choice(np.where(ytr == cl)[0], k, replace=False) for cl in range(5, 10)}
                P, lab = [], []
                for cl in range(5):
                    P.append(oldp[cl]); lab += [cl] * len(oldp[cl])
                for cl in range(5, 10):
                    pr = ztr[idx[cl]].mean(0, keepdims=True) if newmode == "mean" else ztr[idx[cl]]
                    P.append(pr); lab += [cl] * len(pr)
                P = np.concatenate(P); lab = np.array(lab)
                d = np.stack([np.abs(zte - p).sum(1) for p in P], 1); p = lab[d.argmin(1)]; nw = yte >= 5
                rows.append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
            a = np.mean(rows, 0); print(f"old prototypes {KOLD:2d}, new {newmode:9s} k={k}: all-10 {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}", flush=True)
