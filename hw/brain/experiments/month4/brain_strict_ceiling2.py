"""Does a richer code raise the ceiling? (20 Oct 2026) DIAGNOSTIC, not a chip design: closed-form ridge readout (float, all data at once) on several codes of the same images, SIMULATED. Codes: base (shipped encoder), s1 (stride-1 encoder),
base + s1 side by side, and base with 64 and 128 detectors per channel. If a richer code does not raise this ceiling, redesigning the code cannot help the chip. usage: DATA_DIR; env DS, NPS."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import feature_layer
from cortex_core import load
import detector_learn
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); NPS = int(os.environ.get("NPS", 2000)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]; Y = np.eye(10, dtype=np.float32)[ytr]


def codes(kind, F=32):
    feature_layer.PS, feature_layer.ST = (5, 1) if kind == "s1" else (5, 2)
    fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])], F=F)
    if kind == "s1":
        for f in fes: f.pool = 4
    e = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)]).astype(np.float32)
    return e(xtr), e(xte)


def ridge(ctr, cte):
    mu = ctr.mean(0); A = ctr - mu; G = A.T @ A; B = A.T @ (Y - Y.mean(0)); best = 0
    for lam in (30.0, 100.0, 300.0, 1000.0):
        W = np.linalg.solve(G + lam * np.eye(G.shape[0], dtype=np.float32), B); best = max(best, float((((cte - mu) @ W).argmax(1) == yte).mean()))
    return best


b, s1 = codes("base"), codes("s1")
print(DS, "base 4,608 bits ", round(ridge(*b), 4), flush=True); print(DS, "s1 4,608 bits   ", round(ridge(*s1), 4), flush=True)
print(DS, "base + s1 9,216 bits", round(ridge(np.concatenate([b[0], s1[0]], 1), np.concatenate([b[1], s1[1]], 1)), 4), flush=True)
b64 = codes("base", 64); print(DS, "base 64 detectors 9,216 bits", round(ridge(*b64), 4), flush=True)
