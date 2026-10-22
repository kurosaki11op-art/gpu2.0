"""Noisy-copy training for images (21 Oct 2026) SIMULATED. As for words: in every stage the chip learns each clean image and then one altered copy of it (same label). Staged (5 stages of 2 classes), margin 256 / 1,500 dreams / 1 night, 3 seeds; test on the clean images (rule 12: clothing staged >= 83.3, digits staged >= 95.5) and on dropout-damaged test images.
Alterations: drop = 10 % of the image's lit pixels removed; gauss = pixel noise (sd 25 grey levels); shift = the image moved one pixel in a random direction; mix = one of the three at random. usage: DATA_DIR; env DS, SEEDS"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; SEEDS = int(os.environ.get("SEEDS", 3))
for DS in os.environ.get("DS", "fashion,mnist").split(","):
    xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]; ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
    fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
    shp = xtr.shape[1:]; r = np.random.RandomState(3); f32 = lambda x: x.astype(np.float32)
    def alter(x, kind):
        k = kind if kind != "mix" else ("drop", "gauss", "shift")[r.randint(3)]
        if k == "drop": return (x * (r.rand(*x.shape) >= 0.10)).astype(x.dtype)
        if k == "gauss": return np.clip(f32(x) + r.randn(*x.shape) * 25, 0, 255).astype(x.dtype)
        out = np.empty_like(x)
        for i in range(len(x)):
            dy, dx = r.randint(-1, 2), r.randint(-1, 2); out[i] = np.roll(np.roll(x[i].reshape(28, 28), dy, 0), dx, 1).reshape(-1)
        return out
    ctr, cte = enc(xtr), enc(xte); cdrop = enc((xte * (np.random.RandomState(8).rand(*xte.shape) >= 0.25)).astype(xte.dtype))
    for kind in ("none", "drop", "gauss", "shift", "mix"):
        cp = None if kind == "none" else enc(alter(xtr, kind)); acc, accd, accone = [], [], []
        for seed in range(1, SEEDS + 1):
            m = CortexSlow(ctr.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)
            for i, s in enumerate(STAGES):
                o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
                if cp is not None: m.stage(cp[o], ytr[o])
            acc.append(float((m.predict(cte) == yte).mean())); accd.append(float((m.predict(cdrop) == yte).mean()))
        print(DS, "%-6s staged clean %.4f | test with 25%% of the lit pixels removed %.4f" % (kind, np.mean(acc), np.mean(accd)), flush=True)
