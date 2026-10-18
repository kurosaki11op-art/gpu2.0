"""Unsupervised bit selection (critical-period pruning) for few-shot words: keep only code bits whose activation frequency over the OLD words' training clips lies in [LO, HI] (rare noise bits and always-on bits
carry little information, and with 1-5 recordings they only add overfitting). No labels, no new-word data. Shipped protocol (old 0-4 known, new 5-9 from k = 1, 5 recordings, IMPRINT + short sleep), 3 draws,
single view; also EQUAL (all ten words, k each, from scratch). usage: DATA_DIR. SIMULATED."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
D = sys.argv[1]
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int); ctr, cte = z["tr"], z["te"]
freq = ctr[ytr < 5].mean(0)
print("bits", ctr.shape[1], "active freq quantiles", np.round(np.quantile(freq[freq > 0], [0.1, 0.5, 0.9]), 4), "never active", int((freq == 0).sum()), flush=True)
for lo, hi in ((0, 1.01), (0.002, 1.01), (0.01, 1.01), (0.02, 0.8), (0.05, 0.8), (0.1, 0.8)):
    keep = np.where((freq >= lo) & (freq <= hi))[0]; a_, b_ = ctr[:, keep], cte[:, keep]; out = []
    for k in (1, 5):
        rows = []
        for s in (1, 2, 3):
            g = np.random.RandomState(1000 * s); so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
            sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
            m = CortexInt(len(keep), seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2); m.stage(a_[so], ytr[so]); m.stage(a_[sn], ytr[sn])
            p = (b_.astype(np.int32) @ m.W.T.astype(np.int32)).argmax(1); nw = yte >= 5
            rows.append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
        r = np.mean(rows, 0); out.append(f"k={k}: all {r[0]:.3f} new {r[1]:.3f} old {r[2]:.3f}")
    print(f"freq in [{lo}, {hi}]: {len(keep)} bits | " + " | ".join(out), flush=True)
