"""Does a graded code raise the ceiling? (20 Oct 2026) DIAGNOSTIC, SIMULATED. Same detectors, same images; the 2x2 pooling keeps a small count (how many of the 4 positions fired the feature: thermometer planes >=1, >=2, >=3, >=4)
instead of one OR bit, optionally plus a 'strong match' plane. Closed-form dual ridge readout (float, all data) as a ceiling probe. usage: DATA_DIR; env DS, NPS."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import feature_layer, detector_learn
from feature_layer import patches, binarize, support_filter
from cortex_core import load
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); NPS = int(os.environ.get("NPS", 2000)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]; Y = np.eye(10, dtype=np.float32)[ytr]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])


def enc_counts(f, x, strong=0):
    """pooled counts (B, m, m, F) in 0..pool*pool, and optionally a strong-match count"""
    p, n = patches(support_filter(binarize(x, f.thr), f.support)); B = len(x); flat = p.reshape(-1, p.shape[-1])
    t = np.where(f.cnt >= 0, 1, -1); sc = np.where(flat, 1, -1) @ t.T; w = sc.argmax(1); top = sc.max(1)
    W = w.reshape(B, n, n); on = (p.sum(2) >= f.min_on).reshape(B, n, n); st = (top >= strong).reshape(B, n, n) & on if strong else None
    m = n // f.pool; cnt = np.zeros((B, m, m, f.F), np.uint8); cs = np.zeros((B, m, m, f.F), np.uint8)
    for di in range(f.pool):
        for dj in range(f.pool):
            ww = W[:, di:m * f.pool:f.pool, dj:m * f.pool:f.pool]; oo = on[:, di:m * f.pool:f.pool, dj:m * f.pool:f.pool]; bi, ii, jj = np.nonzero(oo)
            np.add.at(cnt, (bi, ii, jj, ww[bi, ii, jj]), 1)
            if strong:
                ss = st[:, di:m * f.pool:f.pool, dj:m * f.pool:f.pool]; bi, ii, jj = np.nonzero(ss); np.add.at(cs, (bi, ii, jj, ww[bi, ii, jj]), 1)
    return cnt.reshape(B, -1), cs.reshape(B, -1)


def build(x, planes, strong=0):
    out = []
    for i in range(0, len(x), 1000):
        parts = []
        for f in fes:
            c, s = enc_counts(f, x[i:i + 1000], strong)
            for k in planes: parts.append(c >= k)
            if strong: parts.append(s >= 1)
        out.append(np.concatenate(parts, 1).astype(np.float32))
    return np.concatenate(out)


def ridge(ctr, cte):
    mu = ctr.mean(0); A = ctr - mu; Kt = A @ A.T; Kte = (cte - mu) @ A.T; best = 0
    for lam in (30.0, 100.0, 300.0, 1000.0, 3000.0):
        al = np.linalg.solve(Kt + lam * np.eye(len(Kt), dtype=np.float32), Y - Y.mean(0)); best = max(best, float(((Kte @ al).argmax(1) == yte).mean()))
    return best


for name, planes, strong in (("OR (shipped)", (1,), 0), ("count>=1,2", (1, 2), 0), ("count>=1,2,3,4", (1, 2, 3, 4), 0), ("OR + strong match (22/25)", (1,), 22), ("count>=1,2 + strong", (1, 2), 22)):
    a, b = build(xtr, planes, strong), build(xte, planes, strong); print(DS, name, a.shape[1], "bits", round(ridge(a, b), 4), flush=True)
