"""Table-score embedding for new words, second round (20 Oct): integer-friendly variants, scaling with the number of known words, and a hybrid with the plain table.
Embedding of a clip = integer table scores over the known classes (SC words 0-4 + NK FSDD digits). Variants: 'raw' (scores as they are), 'max' (score minus the clip's best score, a subtraction and compare per class),
'cen' (float centring, reference). Distance: L1 (adds, abs). Prototypes: sums of embeddings of k recordings (new words) / of the training clips (old words), all compared with the same L1 on MEANS (equal k per new word, so
the mean is a shift when k is a power of two; here exact means). Hybrid: if the plain table's top-two margin (table trained on the 5 old words only, no new rows) exceeds MARGIN the table's old-word answer stands, else the
embedding decides (MARGIN from a development subset of old-word training clips, never test clips). 3 draws, single view, SIMULATED. usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
D = sys.argv[1]
c = np.load(os.path.join(D, "word_codes_shipped.npz")); ctr, cte, cfs, yfs = c["tr"], c["te"], c["fs"], c["yfs"].astype(int) + 10
f = np.load(os.path.join(D, "speech_framesums_int.npz")); y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int)
old = np.where(ytr < 5)[0]; g0 = np.random.RandomState(0)
for NK in (2, 5, 10):
    digits = list(range(10, 10 + NK)); sel = np.isin(yfs, digits)
    m = CortexInt(ctr.shape[1], n_cls=20, seed=1, night=0, daydream=0)
    A = np.concatenate([ctr[old], cfs[sel]]); Y = np.concatenate([ytr[old], yfs[sel]]); pp = g0.permutation(len(Y)); m.stage(A[pp], Y[pp])
    keep = list(range(5)) + digits; W = m.W[keep].astype(np.int32)
    ztr = (ctr.astype(np.int32) @ W.T); zte = (cte.astype(np.int32) @ W.T)
    emb = {"raw": (ztr.astype(np.float32), zte.astype(np.float32)),
           "max": ((ztr - ztr.max(1, keepdims=True)).astype(np.float32), (zte - zte.max(1, keepdims=True)).astype(np.float32)),
           "cen": (ztr - ztr.mean(1, keepdims=True), zte - zte.mean(1, keepdims=True))}
    for k in (1, 5):
        rows = {}
        for s in (1, 2, 3):
            g = np.random.RandomState(1000 * s); idx = {cl: g.choice(np.where(ytr == cl)[0], k, replace=False) for cl in range(5, 10)}
            for name, (etr, ete) in emb.items():
                proto = np.stack([etr[ytr == cl].mean(0) for cl in range(5)] + [etr[idx[cl]].mean(0) for cl in range(5, 10)])
                p = (-np.abs(ete[:, None, :] - proto[None]).sum(2)).argmax(1); nw = yte >= 5
                rows.setdefault(name, []).append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
        for name, v in rows.items():
            a = np.mean(v, 0); print(f"NK={NK:2d} embedding {name} L1 k={k}: all-10 {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}", flush=True)
