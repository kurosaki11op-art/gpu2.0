"""Class-aware feature cells, ceiling probe (20 Oct 2026) SIMULATED. Layer 1: for every pair of classes (a, b), R cells; each cell is an integer perceptron over a random half of the input bits that only learns to tell a from b (its own local label; margin update, adds only, 5 passes over the examples of a and b).
A cell fires when its score is positive (binary hidden code). Layer 2: float dual ridge (ceiling) and the chip's counting table (one pass / 5 stages, margin 256 / 1,500 dreams / 1 night) on the hidden code, or on input + hidden code.
To avoid the hidden code being over-trusted, layer-1 cells learn from a random half of the training examples and layer 2 learns from the other half; the baseline (input code only) uses that same second half. usage: DATA_DIR; env DS, R, MARG."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from numba import njit
import detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); R = int(os.environ.get("R", 4)); MARG = int(os.environ.get("MARG", 64)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
ctr, cte = enc(xtr), enc(xte)
INP = os.environ.get("INPUT", "code")
if INP != "code":
    from feature_layer import binarize
    raw = lambda x: np.concatenate([binarize(x, c).reshape(len(x), -1) for c in (50, 150, ("on", 8), ("off", 8))], 1)
    rtr, rte = raw(xtr), raw(xte); ctr, cte = (rtr, rte) if INP == "raw" else (np.concatenate([ctr, rtr], 1), np.concatenate([cte, rte], 1))
NB = ctr.shape[1]; print("input", INP, NB, "bits", flush=True)


@njit
def learn_cell(w, X, y, mask, margin, epochs, cmax):
    for _ in range(epochs):
        for i in range(len(X)):
            s = 0
            for b in range(X.shape[1]):
                if X[i, b] and mask[b]: s += w[b]
            if y[i] * s <= margin:
                for b in range(X.shape[1]):
                    if X[i, b] and mask[b]:
                        v = w[b] + y[i]; w[b] = cmax if v > cmax else (-cmax if v < -cmax else v)


g = np.random.RandomState(9); perm = g.permutation(len(ytr)); h1, h2 = perm[:len(perm) // 2], perm[len(perm) // 2:]
cells = []
for a in range(10):
    for b in range(a + 1, 10):
        sel = h1[np.isin(ytr[h1], (a, b))]; X = ctr[sel].astype(np.uint8); yy = np.where(ytr[sel] == a, 1, -1).astype(np.int32)
        for r in range(R):
            mask = (g.rand(NB) < 0.5); w = np.zeros(NB, np.int32); order = g.permutation(len(sel)); learn_cell(w, X[order], yy[order], mask, MARG, 5, 15); cells.append(w * mask)
Wc = np.stack(cells).astype(np.float32); print("cells", len(cells), "%.0fs" % (time.time() - t0), flush=True)
hid = lambda c: (c.astype(np.float32) @ Wc.T) > 0
htr, hte = hid(ctr), hid(cte)
Y = np.eye(10, dtype=np.float32)[ytr]


def ridge(a, b, tr):
    a = a[tr].astype(np.float32); b = b.astype(np.float32); mu = a.mean(0); A = a - mu; Kt = A @ A.T; Kte = (b - mu) @ A.T; best = 0
    for lam in (30.0, 100.0, 300.0, 1000.0):
        al = np.linalg.solve(Kt + lam * np.eye(len(Kt), dtype=np.float32), Y[tr] - Y[tr].mean(0)); best = max(best, float(((Kte @ al).argmax(1) == yte).mean()))
    return best


def chip(a, b, staged, seed, tr):
    c = CortexSlow(a.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)
    for i, s in enumerate(STAGES if staged else [tuple(range(10))]):
        o = tr[np.isin(ytr[tr], s)]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; c.stage(a[o], ytr[o])
    return float((c.predict(b) == yte).mean())


for name, a, b in (("input only (second half of the data)", ctr, cte), ("hidden pair cells only", htr, hte), ("input + hidden pair cells", np.concatenate([ctr, htr], 1), np.concatenate([cte, hte], 1))):
    r = {k: round(float(np.mean([chip(a, b, k == "staged", s, h2) for s in (1, 2)])), 4) for k in ("once", "staged")}
    print(DS, name, a.shape[1], "bits | ridge %.4f" % ridge(a, b, h2), "| chip", r, "%.0fs" % (time.time() - t0), flush=True)
