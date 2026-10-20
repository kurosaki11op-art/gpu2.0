"""Dentate-gyrus pattern separation (20 Oct 2026) PROBE, SIMULATED. The shipped code is expanded into M cells, each reading a fixed random subset of the input bits (popcount of the overlap: adds); only the strongest FRAC of cells fire (k winner-take-all), so similar patterns (shirt vs T-shirt) are pushed apart.
Float dual-ridge ceiling and the chip (one pass / 5 stages, margin 256 / 1,500 dreams / 1 night, 3 seeds) on: shipped code, expansion alone, input + expansion. usage: DATA_DIR; env DS, M, FRAC, SUB."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); M = int(os.environ.get("M", 8192)); FRAC = float(os.environ.get("FRAC", 0.03)); SUB = int(os.environ.get("SUB", 96)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]; Y = np.eye(10, dtype=np.float32)[ytr]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
ctr, cte = enc(xtr), enc(xte); NB = ctr.shape[1]
g = np.random.RandomState(7); P = np.zeros((NB, M), np.float32)
for j in range(M): P[g.choice(NB, SUB, replace=False), j] = 1
K = int(FRAC * M)


def expand(c):
    out = np.zeros((len(c), M), bool)
    for i in range(0, len(c), 2000):
        pre = c[i:i + 2000].astype(np.float32) @ P; th = -np.partition(-pre, K, axis=1)[:, K][:, None]; out[i:i + 2000] = pre > th
    return out


etr, ete = expand(ctr), expand(cte); print("expansion", etr.shape, "active", int(etr.sum(1).mean()), "%.0fs" % (time.time() - t0), flush=True)


def ridge(a, b):
    a = a.astype(np.float32); b = b.astype(np.float32); mu = a.mean(0); A = a - mu; Kt = A @ A.T; Kte = (b - mu) @ A.T; best = 0
    for lam in (100.0, 300.0, 1000.0, 3000.0):
        al = np.linalg.solve(Kt + lam * np.eye(len(Kt), dtype=np.float32), Y - Y.mean(0)); best = max(best, float(((Kte @ al).argmax(1) == yte).mean()))
    return best


def chip(a, b, staged, seed):
    c = CortexSlow(a.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)
    for i, s in enumerate(STAGES if staged else [tuple(range(10))]):
        o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; c.stage(a[o], ytr[o])
    return float((c.predict(b) == yte).mean())


for name, a, b in (("shipped code", ctr, cte), ("expansion only", etr, ete), ("input + expansion", np.concatenate([ctr, etr], 1), np.concatenate([cte, ete], 1))):
    r = {k: round(float(np.mean([chip(a, b, k == "staged", s) for s in (1, 2, 3)])), 4) for k in ("once", "staged")}
    print(DS, name, a.shape[1], "bits | ridge %.4f" % ridge(a, b), "| chip", r, "%.0fs" % (time.time() - t0), flush=True)
