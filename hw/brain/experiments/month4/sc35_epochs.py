"""Is the 35-word table under-trained? (19 Oct 2026) Same data presented once (the chip's way, 70.1 %) vs repeated passes (diagnostic: the chip does not keep data), plus a float-weight copy of the same margin-perceptron rule
to separate 'rule' from 'precision'. All 35 words, speaker-disjoint test, 2 seeds. usage: DATA_DIR. SIMULATED."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from cortex_slow import CortexSlow
D = sys.argv[1]
z = np.load(os.path.join(D, "sc35_framesums_int.npz")); y, te = z["y"].astype(int), z["te"]
codes = np.load(os.path.join(D, "sc35_codes_geom3311.npz"))["codes"]
tr_i, te_i = np.where(~te)[0], np.where(te)[0]; ytr, yte = y[tr_i], y[te_i]
for ep in (1, 2, 3, 5):
    a = []
    for s in (1, 2):
        m = CortexSlow(codes.shape[1], n_cls=64, ch=100, K=5, seed=s, night_stop=2, daydream=1)
        for e in range(ep):
            pp = np.random.RandomState(10 * s + e).permutation(len(tr_i)); m.stage(codes[tr_i][pp], ytr[pp])
        a.append((m.predict(codes[te_i]) == yte).mean())
    print(f"chip table, {ep} pass(es) over the data: {np.mean(a):.3f}", flush=True)
