"""Describe a new word by its match to many known words (the idea from the research notes, now testable with 15 known words): the chip is trained on the KNOWN words (SC 0-4 and optionally the 10 FSDD digits);
a clip's embedding is the vector of its table scores over the known classes (integers). New words 5-9 are enrolled as mean-embedding prototypes from k recordings (old SC words: mean embedding of their training clips),
a test clip goes to the nearest prototype (cosine, and L1 after per-clip centring). No new-word table rows are written. 3 draws, single view, SIMULATED.
Variants: embedding from the 5 old classes only | from 15 known classes (5 + 10 digits). usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
D = sys.argv[1]
c = np.load(os.path.join(D, "word_codes_shipped.npz")); ctr, cte, cfs, yfs = c["tr"], c["te"], c["fs"], c["yfs"].astype(int) + 10
f = np.load(os.path.join(D, "speech_framesums_int.npz")); y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int)
old = np.where(ytr < 5)[0]
for variant, ncls in (("5 old classes", 5), ("15 known classes", 15)):
    m = CortexInt(ctr.shape[1], n_cls=20, seed=1, night=0, daydream=0)
    if ncls == 5:
        m.stage(ctr[old], ytr[old]); keep = list(range(5))
    else:
        A = np.concatenate([ctr[old], cfs]); Y = np.concatenate([ytr[old], yfs]); pp = np.random.RandomState(0).permutation(len(Y)); m.stage(A[pp], Y[pp]); keep = list(range(5)) + list(range(10, 20))
    W = m.W[keep].astype(np.int32)
    ztr = (ctr.astype(np.int32) @ W.T).astype(np.float32); zte = (cte.astype(np.int32) @ W.T).astype(np.float32)
    cen = lambda z: z - z.mean(1, keepdims=True)
    for k in (1, 5):
        rows = {"cosine": [], "L1": []}
        for s in (1, 2, 3):
            g = np.random.RandomState(1000 * s)
            idx = {cl: g.choice(np.where(ytr == cl)[0], k, replace=False) for cl in range(5, 10)}
            zc_tr, zc_te = cen(ztr), cen(zte)
            proto = np.stack([zc_tr[ytr == cl].mean(0) for cl in range(5)] + [zc_tr[idx[cl]].mean(0) for cl in range(5, 10)])
            for name in ("cosine", "L1"):
                if name == "cosine":
                    pn = proto / np.linalg.norm(proto, axis=1, keepdims=True); zn = zc_te / np.linalg.norm(zc_te, axis=1, keepdims=True); p = (zn @ pn.T).argmax(1)
                else:
                    p = (-np.abs(zc_te[:, None, :] - proto[None]).sum(2)).argmax(1)
                nw = yte >= 5; rows[name].append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
        for name, v in rows.items():
            a = np.mean(v, 0); print(f"embedding from {variant:17s} {name:6s} k={k}: all-10 {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}", flush=True)
