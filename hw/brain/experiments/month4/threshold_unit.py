"""On-chip threshold unit (22 Oct 2026) SIMULATED. Does the chip's own streaming quantile (cross_modal.quantile_track: compares, adds and shifts) find the second-look threshold, and are the integer cue thresholds (cross_modal.cue_thresholds) as good as the exact ones? Clothing and digits, 10,000 training images (5 stages), shipped table A (coarse code); the threshold is learned from the margins of an UNLABELLED stream (the training images in random order) and applied to the test images.
usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, detector_learn, cross_modal
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
sc = lambda m, c: np.where(m.known[None, :], c.astype(np.int32) @ m.S.T.astype(np.int32), -(1 << 28)).astype(np.int64)
for DS in ("fashion", "mnist"):
    xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
    fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
    ctr, cte = enc(xtr), enc(xte); m = CortexSlow(ctr.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=1, margin=256, ndream=1500, night=1)
    o = np.random.RandomState(1).permutation(len(ytr)); m.stage(ctr[o], ytr[o]); sa_tr, sa_te = sc(m, ctr), sc(m, cte)
    mg = lambda s: np.sort(s, 1)[:, -1] - np.sort(s, 1)[:, -2]; mtr, mte = mg(sa_tr), mg(sa_te); stream = mtr[np.random.RandomState(2).permutation(len(mtr))]
    for n in (3, 6, 8):                                       # target share of inputs below the threshold: n/16
        exact = float(np.percentile(mtr, 100 * n / 16))
        for e0, k in ((9, 6), (9, 7), (10, 7), (8, 8)):
            q = cross_modal.quantile_track(stream.tolist(), n, e0, k)[-1]; share = float((mte < q).mean())
            print(DS, "share %2d/16 = %.3f: exact threshold %7.0f, chip estimate %7d (e0 %d, k %d), share of test inputs below it %.3f" % (n, n / 16, exact, q, e0, k, share), flush=True)
    ref = float(np.median(mtr)); T_exact = np.array([int(np.ceil(ref * 2 ** (kk - 0.5))) for kk in range(-3, 4)]); T_int = np.array(cross_modal.cue_thresholds(int(ref)))
    print(DS, "median margin %.0f; cue thresholds exact %s, integer %s, max difference %d" % (ref, T_exact.tolist(), T_int.tolist(), int(np.abs(T_exact - T_int).max())), flush=True)
