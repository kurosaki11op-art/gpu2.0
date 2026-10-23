"""Does fewer bits cost accuracy? (23 Oct 2026) SIMULATED. Integer model of L Cortex on MNIST (or Fashion-MNIST with env DS=fashion), shipped settings, slow table, 2,000 images
per stage, 2 seeds. Sweeps (a) the width of the fast table counters (clamp +-cmax: 2 to 8 bits) and (b) the width of the dream counts (6 to 12 bits).
Two protocols: 5 stages of 2 classes (forgetting test) and all classes at once (one stage). usage: python bits_vs_accuracy.py DATA_DIR"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from feature_layer import Features
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; NPS = 2000; SEEDS = int(os.environ.get("SEEDS", 2)); t0 = time.time()
DS = os.environ.get("DS", "mnist"); xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
fes = [Features(32, thr=c, pool=2).fit(xtr[np.isin(ytr, STAGES[0])][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
enc = lambda x: np.concatenate([f.encode(x) for f in fes], 1)
rs = np.random.RandomState(1)
idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); te = rs.permutation(len(xte))[:3000]
ctr, ytr_s = enc(xtr[idx]), ytr[idx]; cte, yte_s = enc(xte[te]), yte[te]; nb = ctr.shape[1]
print("codes ready %.0fs" % (time.time() - t0), flush=True)


def run(cmax, B, seed, staged):
    m = CortexSlow(nb, ch=max(100, NPS >> 5), K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1, cmax=cmax, B=B)
    r = np.random.RandomState(seed)
    if staged:
        for s in STAGES:
            sel = np.isin(ytr_s, s); o = r.permutation(sel.sum()); m.stage(ctr[sel][o], ytr_s[sel][o])
    else:
        o = r.permutation(len(ytr_s)); m.stage(ctr[o], ytr_s[o])
    return 100 * float((m.predict(cte) == yte_s).mean())


print("| what changes | bits | staged % | all at once % |", flush=True); print("|---|---|---|---|", flush=True)
for label, cmax, B, bits in (("fast table", 1, 10, 2), ("fast table", 3, 10, 3), ("fast table", 7, 10, 4), ("fast table (shipped)", 15, 10, 5), ("fast table", 31, 10, 6),
                             ("fast table", 63, 10, 7), ("fast table", 127, 10, 8), ("dream counts", 15, 6, 6), ("dream counts", 15, 8, 8), ("dream counts", 15, 12, 12)):
    st = np.mean([run(cmax, B, s, True) for s in range(1, SEEDS + 1)]); al = np.mean([run(cmax, B, s, False) for s in range(1, SEEDS + 1)])
    shown = bits if label.startswith("fast") else B
    print("| %s | %d | %.2f | %.2f |  (%.0fs)" % (label, shown, st, al, time.time() - t0), flush=True)
