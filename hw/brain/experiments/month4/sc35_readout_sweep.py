"""Readout settings of the chip table on the 35-word set (19 Oct 2026): weight range (cmax 15 = 5 bit, 31 = 6 bit, 63 = 7 bit), margin, dream count, night length; all 35 words together, speaker-disjoint test, 2 seeds.
Baseline (shipped settings) 70.1 %. usage: DATA_DIR. SIMULATED."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from cortex_slow import CortexSlow
D = sys.argv[1]
z = np.load(os.path.join(D, "sc35_framesums_int.npz")); y, te = z["y"].astype(int), z["te"]
codes = np.load(os.path.join(D, "sc35_codes_geom3311.npz"))["codes"]
tr_i, te_i = np.where(~te)[0], np.where(te)[0]; ytr, yte = y[tr_i], y[te_i]
base = dict(ch=100, K=5, night_stop=2, daydream=1)
for name, kw in (("shipped", {}), ("cmax31", dict(cmax=31)), ("cmax63", dict(cmax=63)), ("margin16", dict(margin=16)), ("margin64", dict(margin=64)), ("margin128 cmax31", dict(margin=128, cmax=31)),
                 ("ndream12000", dict(ndream=12000)), ("night4", dict(night=4)), ("cmax31 night4 ndream12000", dict(cmax=31, night=4, ndream=12000)), ("no daydream", dict(daydream=0)),
                 ("margin64 cmax31", dict(margin=64, cmax=31))):
    a = []
    for s in (1, 2):
        m = CortexSlow(codes.shape[1], n_cls=64, seed=s, **{**base, **kw}); pp = np.random.RandomState(s).permutation(len(tr_i)); m.stage(codes[tr_i][pp], ytr[pp]); a.append((m.predict(codes[te_i]) == yte).mean())
    print(f"{name}: {np.mean(a):.3f}", flush=True)
