"""Detector coverage test (20 Oct 2026) DIAGNOSTIC, SIMULATED. Shipped: detectors learned from the first stage's two classes only. Test: detectors learned (same on-chip rule, no labels) from images of all classes, or from 2 classes per stage pooled (first 2, first 4, first 6 classes).
Evaluate: float ridge ceiling, chip one-pass, chip staged (margin 256 / 1,500 dreams / 1 night, seed 1). usage: DATA_DIR; env DS, NPS."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); NPS = int(os.environ.get("NPS", 2000)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]; Y = np.eye(10, dtype=np.float32)[ytr]


def ridge(ctr, cte):
    ctr = ctr.astype(np.float32); cte = cte.astype(np.float32); mu = ctr.mean(0); A = ctr - mu; Kt = A @ A.T; Kte = (cte - mu) @ A.T; best = 0
    for lam in (100.0, 300.0, 1000.0):
        al = np.linalg.solve(Kt + lam * np.eye(len(Kt), dtype=np.float32), Y - Y.mean(0)); best = max(best, float(((Kte @ al).argmax(1) == yte).mean()))
    return best


def chip(ctr, cte, staged):
    c = CortexSlow(ctr.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=1, margin=256, ndream=1500, night=1)
    for i, s in enumerate(STAGES if staged else [tuple(range(10))]):
        o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 + i).permutation(len(o))]; c.stage(ctr[o], ytr[o])
    return float((c.predict(cte) == yte).mean())


for name, ns in (("first 2 classes (shipped)", 1), ("first 4 classes", 2), ("first 6 classes", 3), ("all 10 classes", 5)):
    src = xtr[np.isin(ytr, sum(STAGES[:ns], ()))]; fes = detector_learn.learn_features(src)
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
    ctr, cte = enc(xtr), enc(xte)
    print(DS, "detectors from", name, "(%d images)" % len(src), "ridge %.4f" % ridge(ctr, cte), "chip one-pass %.4f" % chip(ctr, cte, False), "chip staged %.4f" % chip(ctr, cte, True), "%.0fs" % (time.time() - t0), flush=True)
