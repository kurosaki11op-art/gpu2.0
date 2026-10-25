"""25 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. The connected structure (the DNA idea) over L's LEARNED detector bits instead of pixels.
Code layout (stride 1, pool 4): bit = channel*1152 + (i*6 + j)*32 + f, i.e. 4 channels x 6x6 cells x 32 detectors.
Each bit is judged by NSP spatial neighbours (the same detector in the cells to the left, above, above-left, above-right; out of the grid counts as off) and NCELL partners chosen by the data: the bits of the same cell and channel that co-fire most with it (counted correlation, learned wiring, no labels).
Class-conditional counted tables P(bit | neighbour bits); image scored by the log-likelihood under each class (adds of table entries). Mixing weight with L's table is chosen on a validation split of the training images.
env: NSP (1 to 4), NCELL (0 to 6)"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, report, CL
E = lambda k, d: type(d)(os.environ.get(k, d))
NSP, NCELL = E("NSP", 3), E("NCELL", 3); NB = NSP + NCELL; NCTX = 1 << NB; M = 6; F = 32; CH = 4; NBITS = CH * M * M * F
ntr = 50000; t0 = time.time()
# learned wiring inside each cell and channel: partners = most correlated other detectors (by counted correlation on the first 20,000 training codes)
X = ctr[:20000].reshape(-1, CH, M * M, F).astype(np.float32); partner = np.zeros((CH, M * M, F, max(NCELL, 1)), np.int64)
for ch in range(CH):
    for c in range(M * M):
        A = X[:, ch, c, :]; mu = A.mean(0); sd = A.std(0) + 1e-6; R = ((A - mu) / sd).T @ ((A - mu) / sd) / len(A); np.fill_diagonal(R, 0)
        partner[ch, c] = np.argsort(-np.abs(R), 1)[:, :max(NCELL, 1)]
del X
conn = np.full((NBITS, NB), -1, np.int64)                                         # index of the neighbour bit, -1 = off
SPN = [(0, -1), (-1, 0), (-1, -1), (-1, 1)][:NSP]
for ch in range(CH):
    for i in range(M):
        for j in range(M):
            for f in range(F):
                b = ch * M * M * F + (i * M + j) * F + f; k = 0
                for di, dj in SPN:
                    ii, jj = i + di, j + dj
                    if 0 <= ii < M and 0 <= jj < M: conn[b, k] = ch * M * M * F + (ii * M + jj) * F + f
                    k += 1
                for q in range(NCELL): conn[b, k] = ch * M * M * F + (i * M + j) * F + partner[ch, i * M + j, f, q]; k += 1
valid = conn >= 0; connc = np.where(valid, conn, 0); wts = (1 << np.arange(NB))[None, :]
def ctx(C):
    nb = C[:, connc]; nb = nb * valid[None]; return (nb.astype(np.int64) * wts[None]).sum(2)                    # (N, NBITS)
base = (np.arange(NBITS) * NCTX)[None, :]
def fit():
    lt = np.zeros((10, NBITS * NCTX), np.float32); l1 = np.zeros_like(lt)
    for c in range(10):
        idx_c = np.where(ytr[:ntr] == c)[0]; n = np.zeros(NBITS * NCTX); s = np.zeros(NBITS * NCTX)
        for i in range(0, len(idx_c), 1000):
            Cc = ctr[idx_c[i:i + 1000]]; ix = (base + ctx(Cc)).ravel(); n += np.bincount(ix, minlength=NBITS * NCTX); s += np.bincount(ix, weights=Cc.ravel(), minlength=NBITS * NCTX)
        t = (s + 0.5) / (n + 1.0); lt[c] = np.log(t); l1[c] = np.log(1 - t)
    return lt, l1
def loglik(C, lt, l1):
    out = np.zeros((len(C), 10), np.float32)
    for i in range(0, len(C), 1000):
        Ci = C[i:i + 1000].astype(np.float32); ix = base + ctx(C[i:i + 1000])
        for c in range(10): out[i:i + 1000, c] = (Ci * lt[c][ix] + (1 - Ci) * l1[c][ix]).sum(1)
    return out
lt, l1 = fit(); print("[%4.0fs] NSP=%d NCELL=%d: %d context bits, %d contexts per bit, %.1f M table entries per class fitted" % (time.time() - t0, NSP, NCELL, NB, NCTX, NBITS * NCTX / 1e6), flush=True)
lv = loglik(ctr[ntr:], lt, l1); ltest = loglik(cte, lt, l1); print("[%4.0fs] scored" % (time.time() - t0), flush=True)
report("connected generative over L's detector bits (%d + %d)" % (NSP, NCELL), ltest)
W = train_table(ctr[:ntr], ytr[:ntr]); Sv = ctr[ntr:].astype(np.int32) @ W; St = cte.astype(np.int32) @ W; yv = ytr[ntr:]
def z(S): return (S - S.mean(1, keepdims=True)) / (S.std() + 1e-9)
best = (-1, 0)
for a in (0, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
    acc = ((z(Sv) + a * z(lv)).argmax(1) == yv).mean(); best = max(best, (acc, a))
print("validation: mixing weight %.2f gives %.4f (table alone %.4f); generative alone %.4f" % (best[1], best[0], (Sv.argmax(1) == yv).mean(), (lv.argmax(1) == yv).mean()))
report("L table alone (trained on 50,000)", St)
report("L table + connected detector model, weight %.2f" % best[1], z(St) + best[1] * z(ltest))
