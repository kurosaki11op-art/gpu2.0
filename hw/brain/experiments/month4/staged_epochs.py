"""Two (or three) passes over the CURRENT stage's examples (20 Oct 2026) SIMULATED. No stored past data: the stage's own examples are available that day and are shown again before sleep (shuffled), with the chip's dreams of old classes each time. Clothing and digits, 5 stages, margin 256 / 1,500 dreams / 1 night, 5 seeds, passes 1 / 2 / 3. usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
for DS in ("fashion", "mnist"):
    xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]; ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
    fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)]); ctr, cte = enc(xtr), enc(xte)
    for passes in (1, 2, 3):
        a = []
        for seed in range(1, 6):
            m = CortexSlow(ctr.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)
            for i, s in enumerate(STAGES):
                o = np.where(np.isin(ytr, s))[0]
                for p in range(passes): oo = o[np.random.RandomState(100 * seed + i + 7 * p).permutation(len(o))]; m.stage(ctr[oo], ytr[oo])
            a.append(float((m.predict(cte) == yte).mean()))
        print(DS, "passes over the stage's own examples:", passes, "staged accuracy %.4f" % np.mean(a), flush=True)
