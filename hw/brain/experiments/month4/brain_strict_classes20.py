"""Many classes (22 Oct 2026) SIMULATED. 20 classes = the 10 digits (labels 0-9) and the 10 clothing classes (labels 10-19) as one problem, 10 stages of 2 classes, NPS training images per stage, the full test sets (20,000 images). The retina detectors are learned on the first stage only (digits 0, 1), as the chip would. Settings margin 256 / 1,500 dreams per old class / 1 night; follow interval max(100, NPS / 30). Arms: shipped table, tail memory (3/16). One pass vs staged.
usage: DATA_DIR; env NPS, SEEDS"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
import cortex_rules
D = sys.argv[1]; NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 2)); t0 = time.time(); os.environ["TMIX"] = "3"
a = load(D, "mnist"); b = load(D, "fashion")
xtr = np.concatenate([a[0], b[0]]); ytr = np.concatenate([a[1].astype(np.int64), b[1].astype(np.int64) + 10]); xte = np.concatenate([a[2], b[2]]); yte = np.concatenate([a[3].astype(np.int64), b[3].astype(np.int64) + 10])
STAGES = [(2 * i, 2 * i + 1) for i in range(10)]; rs = np.random.RandomState(5)
idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])][:12000]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
ctr, cte = enc(xtr), enc(xte); print("train", ctr.shape, "test", cte.shape, "%.0fs" % (time.time() - t0), flush=True)
for arm in ("base", "tail"):
    for staged in (False, True):
        acc, accd, accc = [], [], []
        for seed in range(1, SEEDS + 1):
            kw = dict(n_cls=20, ch=max(100, NPS // 30), K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)
            m = CortexSlow(ctr.shape[1], **kw) if arm == "base" else cortex_rules.CortexRules(ctr.shape[1], rule="tailmem", **kw)
            for i, s in enumerate(STAGES if staged else [tuple(range(20))]):
                o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
            p = m.predict(cte); acc.append(float((p == yte).mean())); accd.append(float((p == yte)[yte < 10].mean())); accc.append(float((p == yte)[yte >= 10].mean()))
        print("20 classes", arm, "staged" if staged else "one pass", "all %.4f | digits %.4f | clothing %.4f" % (np.mean(acc), np.mean(accd), np.mean(accc)), "%.0fs" % (time.time() - t0), flush=True)
