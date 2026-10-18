"""Calibration fixes for new classes (from the GPU few-shot / class-incremental literature, made multiplier-free), words 0-4 known then 5-9 from k recordings (IMPRINT + short sleep, aligned codes).
Applied at decision time on the table scores (integers):
  logit   : bias_c = ALPHA * (blen(n_max) - blen(n_c))   (logit adjustment by log class frequency; rare classes boosted; blen = bit length, no multiply except by the integer ALPHA)
  cosine  : score_c >> blen(mass_c) * 2^M   (rows normalised by their L1 mass rounded to a power of two, shift only)
  both    : cosine then logit.
Accuracy over all ten words / new words (10-way) / old words, 3 draws, single view. SIMULATED. usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
D = sys.argv[1]
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int); ctr, cte = z["tr"], z["te"].astype(np.int32)
bl = lambda v: np.array([int(x).bit_length() for x in v])
for k in (1, 2, 5):
    rows = {}
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s); so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
        sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
        m = CortexInt(ctr.shape[1], seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2); m.stage(ctr[so], ytr[so]); m.stage(ctr[sn], ytr[sn])
        W = m.W.astype(np.int64); sc = cte @ W.T.astype(np.int32); n = m.n.astype(np.int64)
        nb = bl(n[:10]); mass = np.abs(W).sum(1); mb = bl(mass)
        variants = {"plain": sc.astype(np.int64)}
        for a in (4, 8, 16, 32, 64):
            variants[f"logit{a}"] = sc + a * (nb.max() - nb)[None, :]
        cs = (sc.astype(np.int64) << 12) >> mb[None, :]
        variants["cosine"] = cs
        for a in (4, 16, 64):
            variants[f"cosine+logit{a}"] = cs + (a * (nb.max() - nb))[None, :] * 4
        for name, v in variants.items():
            p = v.argmax(1); nw = yte >= 5
            rows.setdefault(name, []).append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
    for name, v in rows.items():
        a = np.mean(v, 0); print(f"k={k} {name:14s}: all-10 {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}", flush=True)
