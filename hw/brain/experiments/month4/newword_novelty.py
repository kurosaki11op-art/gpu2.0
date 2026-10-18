"""Novelty gate for new spoken words (idea, 19 Oct): the chip knows words 0-4, learns 5-9 from k recordings. A clip whose best OLD-class score is low is probably a new word:
if (best old score) < tau * (mean best-old-score of the old words' own training clips) the answer is chosen among the NEW classes only. tau swept (oracle sweep, then a rule
fixed from the old words' training score spread). Accuracy over all 10 words, 3 draws, single view. SIMULATED. usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
D = sys.argv[1]
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int); ctr, cte = z["tr"].astype(np.int32), z["te"].astype(np.int32)
for k in (1, 5):
    res = {}
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s); so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
        sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
        m = CortexInt(ctr.shape[1], seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2); m.stage(ctr[so], ytr[so])
        Wold = m.W.T.astype(np.int32).copy()
        m.stage(ctr[sn], ytr[sn]); W = m.W.T.astype(np.int32)
        sc = cte @ W; bo = sc[:, :5].max(1)
        ref = (ctr[so][:3000] @ W)[:, :5].max(1); mu, sd = ref.mean(), ref.std()
        for tau in (0.0, 0.5, 0.7, 0.8, 0.9, 1.0, 1.1):
            gate = bo < tau * mu
            p = np.where(gate, sc[:, 5:].argmax(1) + 5, sc.argmax(1))
            res.setdefault(tau, []).append(((p == yte).mean(), (p[yte >= 5] == yte[yte >= 5]).mean(), (p[yte < 5] == yte[yte < 5]).mean()))
    for tau, v in res.items():
        a = np.mean(v, 0); print(f"k={k} tau={tau}: all {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}", flush=True)
