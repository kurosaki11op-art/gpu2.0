"""25 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. Wider connected structure: each bit is judged from NB neighbouring bits (counted tables per class and position, 2^NB contexts). Same protocol as connected_model.py: mixing weight with L's table chosen on a validation split of the training images.
env: NB in {3, 5, 7, 9}"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, xte, ytr, yte, ctr, cte, train_table, report, CL
NB = int(os.environ.get("NB", 7))
OFFS = [(0, -1), (-1, 0), (-1, -1), (-1, 1), (0, -2), (-2, 0), (-1, -2), (-1, 2), (-2, -1), (-2, 1)]            # (dy, dx) in the same threshold plane, nearest first; plus the lower-threshold bit at the same pixel
def planes(x):
    im = x.reshape(-1, 28, 28); return np.stack([im > 85, im > 170], 1).astype(np.int8)
def context(P):
    n = len(P); Cx = np.zeros(P.shape, np.int64); k = 0
    for dy, dx in OFFS[:NB - 1]:
        S = np.zeros_like(P); ys, yd = (slice(0, 28 - dy), slice(dy, 28)) if dy >= 0 else (slice(-dy, 28), slice(0, 28 + dy)); xs, xd = (slice(0, 28 - dx), slice(dx, 28)) if dx >= 0 else (slice(-dx, 28), slice(0, 28 + dx))
        S[:, :, yd, xd] = P[:, :, ys, xs]; Cx += S.astype(np.int64) << k; k += 1
    lo = np.zeros_like(P); lo[:, 1] = P[:, 0]; Cx += lo.astype(np.int64) << k; return Cx
NCTX = 1 << NB; pos = (np.arange(2)[:, None, None] * 28 + np.arange(28)[None, :, None]) * 28 + np.arange(28)[None, None, :]
def flat(P):
    return (pos[None] * NCTX + context(P)).reshape(len(P), -1)
def fit(P, y):
    size = 2 * 28 * 28 * NCTX; lt = np.zeros((10, size), np.float32); l1 = np.zeros((10, size), np.float32)
    for c in range(10):
        Pc = P[y == c]; idx = flat(Pc); n = np.bincount(idx.ravel(), minlength=size); s = np.bincount(idx.ravel(), weights=Pc.reshape(len(Pc), -1).ravel(), minlength=size)
        t = (s + 0.5) / (n + 1.0); lt[c] = np.log(t); l1[c] = np.log(1 - t)
    return lt, l1
def loglik(P, tabs):
    lt, l1 = tabs; out = np.zeros((len(P), 10), np.float32)
    for i in range(0, len(P), 2000):
        Pi = P[i:i + 2000]; idx = flat(Pi); b = Pi.reshape(len(Pi), -1)
        for c in range(10): out[i:i + 2000, c] = (b * lt[c][idx] + (1 - b) * l1[c][idx]).sum(1)
    return out
t0 = time.time(); ntr = 50000; Ptr, Pte = planes(xtr), planes(xte)
tabs = fit(Ptr[:ntr], ytr[:ntr]); lv = loglik(Ptr[ntr:], tabs); lt = loglik(Pte, tabs); print("[%3.0fs] NB=%d contexts per bit %d, table entries per class %d fitted" % (time.time() - t0, NB, NCTX, 2 * 784 * NCTX), flush=True)
report("connected generative model alone, %d neighbour bits" % NB, lt)
W = train_table(ctr[:ntr], ytr[:ntr]); Sv = ctr[ntr:].astype(np.int32) @ W; St = cte.astype(np.int32) @ W; yv = ytr[ntr:]
def z(S): return (S - S.mean(1, keepdims=True)) / (S.std() + 1e-9)
best = (-1, 0)
for a in (0, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
    acc = ((z(Sv) + a * z(lv)).argmax(1) == yv).mean(); best = max(best, (acc, a))
print("validation: mixing weight %.2f gives %.4f (table alone %.4f); generative alone on validation %.4f" % (best[1], best[0], (Sv.argmax(1) == yv).mean(), (lv.argmax(1) == yv).mean()))
report("L table + connected generative (%d bits), weight %.2f" % (NB, best[1]), z(St) + best[1] * z(lt))
