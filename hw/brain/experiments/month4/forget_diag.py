"""Where does the staged loss come from? (20 Oct 2026) per-class accuracy staged vs one-pass, clothing, shipped rule, SIMULATED. usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; CFG = dict(margin=256, ndream=1500, night=1)
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
ctr, cte = enc(xtr), enc(xte); NB = ctr.shape[1]
for mode in ("once", "staged"):
    m = CortexSlow(NB, ch=100, K=5, night_stop=2, daydream=1, seed=1, **CFG)
    for i, s in enumerate(STAGES if mode == "staged" else [tuple(range(10))]):
        o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
        if mode == "staged":
            p = m.predict(cte); seen = np.isin(yte, sum(STAGES[:i + 1], ())); print("after stage", i, "seen-class acc %.3f" % (p[seen] == yte[seen]).mean(), "new-pair acc %.3f" % (p[np.isin(yte, s)] == yte[np.isin(yte, s)]).mean(), flush=True)
    p = m.predict(cte); print(mode, "per-class", [round(float((p[yte == c] == c).mean()), 2) for c in range(10)], "total %.4f" % (p == yte).mean(), flush=True)
