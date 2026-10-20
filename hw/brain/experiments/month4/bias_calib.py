"""Intrinsic-plasticity bias (20 Oct 2026) PROBE, SIMULATED. After the 5 stages (shipped chip, margin 256 / 1,500 dreams / 1 night) one integer bias per class is added to the class scores; it is tuned so that no class wins more or less than its share:
each round, for every class c, bias[c] += step if c's own examples are missed more often than c steals other classes' examples, -= step otherwise (compares and adds). Calibration data: (a) DREAMS only (generated from the dream memory, nothing stored: the brain-principled version), (b) the real training examples (a cheating bound).
Also prints where the old classes' errors go (confusion toward the newest classes). usage: DATA_DIR; env DS."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
ctr, cte = enc(xtr), enc(xte)


def calibrate(S, Z, zy, rounds=40, step=None):
    sc = Z.astype(np.int32) @ S.T; step = step or max(1, int(np.median(np.sort(sc, 1)[:, -1] - np.sort(sc, 1)[:, -2]) // 8)); b = np.zeros(S.shape[0], np.int64)
    for _ in range(rounds):
        p = (sc + b).argmax(1)
        for c in range(S.shape[0]):
            miss = ((zy == c) & (p != c)).sum() / max(1, (zy == c).sum()); steal = ((zy != c) & (p == c)).sum() / max(1, (zy != c).sum() / (S.shape[0] - 1))
            b[c] += step if miss > steal else -step
    return b


res = {k: [] for k in ("shipped staged", "bias from dreams", "bias from real data (bound)")}
for seed in (1, 2, 3):
    m = CortexSlow(ctr.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)
    for i, s in enumerate(STAGES): o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
    S = m.S.astype(np.int32); sc_te = cte.astype(np.int32) @ S.T; res["shipped staged"].append(float((sc_te.argmax(1) == yte).mean()))
    g = np.random.RandomState(seed); Zy = np.repeat(np.arange(10), 300); Z = (g.random_sample((len(Zy), ctr.shape[1])) < (m.on[Zy] / np.maximum(m.n[Zy][:, None], 1))).astype(np.uint8)       # dreams from the dream memory
    b1 = calibrate(S, Z, Zy); res["bias from dreams"].append(float(((sc_te + b1).argmax(1) == yte).mean()))
    b2 = calibrate(S, ctr, ytr); res["bias from real data (bound)"].append(float(((sc_te + b2).argmax(1) == yte).mean()))
    if seed == 1:
        p = sc_te.argmax(1); print("per-class accuracy shipped", [round(float((p[yte == c] == c).mean()), 2) for c in range(10)]); print("share predicted per class", [round(float((p == c).mean()), 3) for c in range(10)], "(true share 0.1 each)")
        print("bias from dreams", b1.tolist(), "| from real data", b2.tolist(), flush=True)
for k, v in res.items(): print(DS, k, round(float(np.mean(v)), 4), flush=True)
