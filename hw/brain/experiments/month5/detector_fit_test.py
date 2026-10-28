"""29 Oct 2026 (run 28 Oct), SIMULATED. Does fitting L's detectors on ALL classes instead of only T-shirt+Trouser (the shipped fit) raise L's accuracy? Inference cost is unchanged (same 128 detectors, same encoder).
Fit variants: shipped = classes (0,1), 12,000 images; all10 = 12,000 random images of all classes; all10_big = 30,000. Same table training as shirt_new_methods_setup.train_table. usage: python detector_fit_test.py"""
import os, sys, time
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features
D = "/tmp/fashion"; xtr, ytr, xte, yte = load(D, "fashion"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
CH = (50, 150, ("on", 8), ("off", 8)); rs = np.random.RandomState(0); t0 = time.time()
def run(tag, fit_x):
    fes = [Features(32, thr=c, pool=4).fit(fit_x) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)]).astype(np.uint8)
    ctr, cte = enc(xtr), enc(xte)
    m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel]); W = m.S.T.astype(np.int32)
    S = cte.astype(np.int32) @ W; p = S.argmax(1); srt = np.sort(S, 1); marg = srt[:, -1] - srt[:, -2]
    print("%-12s L alone accuracy %.4f | shirt recall %.3f | active bits %.0f | [%.0fs]" % (tag, (p == yte).mean(), (p[yte == 6] == 6).mean(), cte.sum(1).mean(), time.time() - t0), flush=True)
run("shipped", xtr[np.isin(ytr, (0, 1))][:12000])
run("all10", xtr[rs.choice(len(xtr), 12000, replace=False)])
run("all10_big", xtr[rs.choice(len(xtr), 30000, replace=False)])
