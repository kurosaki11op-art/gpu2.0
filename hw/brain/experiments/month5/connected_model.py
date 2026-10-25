"""25 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. 'Connected structure' test (the DNA idea): every bit is tied to its neighbours (left, above, and the lower-threshold bit at the same pixel), so a part of an image is judged by how well its neighbours predict it.
Class-conditional counted tables P(bit | 3 neighbour bits) per class and position (8 contexts); an image is scored by the log-likelihood of all its bits under each class's connected model (adds of table entries). Compared with the same model that ignores the neighbours (independent bits).
Mixing weight with L's counting table is chosen on a validation split of the training images (last 10,000), never on test. Labels are used only to pick which class's tables to count into, as in L's table."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, xte, ytr, yte, ctr, cte, train_table, report, CL
def planes(x):
    im = x.reshape(-1, 28, 28); return np.stack([im > 85, im > 170], 1).astype(np.int8)
def context(P):
    L = np.zeros_like(P); U = np.zeros_like(P); L[:, :, :, 1:] = P[:, :, :, :-1]; U[:, :, 1:, :] = P[:, :, :-1, :]
    lo = np.zeros_like(P); lo[:, 1] = P[:, 0]; return (L + 2 * U + 4 * lo).astype(np.int64)
def fit(P, y, ctx_on):
    Cx = context(P) if ctx_on else np.zeros(P.shape, np.int64); T = np.zeros((10, 2, 28, 28, 8))
    for c in range(10):
        Pc, Cc = P[y == c], Cx[y == c]
        for k in range(8):
            m = (Cc == k); n = m.sum(0); s = (Pc * m).sum(0); T[c, :, :, :, k] = (s + 0.5) / (n + 1.0)
    return np.log(T), np.log(1 - T)
def loglik(P, tabs, ctx_on):
    lt, l1 = tabs; Cx = context(P) if ctx_on else np.zeros(P.shape, np.int64); out = np.zeros((len(P), 10)); pl, yy, xx = np.meshgrid(np.arange(2), np.arange(28), np.arange(28), indexing="ij")
    for c in range(10): out[:, c] = (P * lt[c][pl, yy, xx, Cx] + (1 - P) * l1[c][pl, yy, xx, Cx]).reshape(len(P), -1).sum(1)
    return out
t0 = time.time(); ntr = 50000
Ptr, Pte = planes(xtr), planes(xte); res = {}
for name, on in (("independent bits", False), ("connected (3 neighbour bits)", True)):
    tabs = fit(Ptr[:ntr], ytr[:ntr], on); res[name] = (loglik(Ptr[ntr:], tabs, on), loglik(Pte, tabs, on)); print("[%3.0fs] %s fitted" % (time.time() - t0, name), flush=True)
    report("generative model alone: " + name, res[name][1])
W = train_table(ctr[:ntr], ytr[:ntr]); Sv = ctr[ntr:].astype(np.int32) @ W; St = cte.astype(np.int32) @ W; yv = ytr[ntr:]
report("L counting table (trained on 50,000)", St)
def z(S): return (S - S.mean(1, keepdims=True)) / (S.std() + 1e-9)
for name in res:
    lv, lt = res[name]; best = (-1, 0)
    for a in (0, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0):
        acc = ((z(Sv) + a * z(lv)).argmax(1) == yv).mean(); best = max(best, (acc, a))
    print("validation: mixing weight %.2f gives %.4f (table alone %.4f)" % (best[1], best[0], ((Sv).argmax(1) == yv).mean()))
    report("L table + generative (%s), weight %.2f" % (name, best[1]), z(St) + best[1] * z(lt))
