"""25 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. L-Genome kill test 1 (docs/L_genome_design.md): learned per-class wiring.
Every detector bit of L's code (4,608 bits = 4 channels x 6x6 cells x 32 detectors) is judged given K=3 parent bits. Candidates for the parents: the other 31 detectors in the same cell and channel, and the same detector in the cells to the left, above, above-left, above-right.
A  fixed spatial parents (left, above, above-left), the same for every class
B  parents chosen by counted mutual information on pooled all-class data, the same for every class
C  parents chosen by counted mutual information inside each class (class-specific wiring: each class has its own structure)
Class-conditional counted tables P(bit | parents), image scored by log-likelihood under each class. Table budget equal for A, B and C (8 contexts per bit per class). Trained on 50,000 images, scored on the 10,000 test images.
env: K (parents, default 3)"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, report, CL
K = int(os.environ.get("K", 3)); NCTX = 1 << K; CHN, M, F = 4, 6, 32; NBITS = CHN * M * M * F; ntr = 50000; t0 = time.time()
SPN = [(0, -1), (-1, 0), (-1, -1), (-1, 1)]
def bit(ch, i, j, f): return ch * M * M * F + (i * M + j) * F + f
nbidx = np.full((len(SPN), NBITS), -1, np.int64)
for ch in range(CHN):
    for i in range(M):
        for j in range(M):
            for f in range(F):
                for q, (di, dj) in enumerate(SPN):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < M and 0 <= jj < M: nbidx[q, bit(ch, i, j, f)] = bit(ch, ii, jj, f)
def stats(idx):
    n = len(idx); s1 = np.zeros(NBITS); same = np.zeros((CHN, M * M, F, F)); spat = np.zeros((len(SPN), NBITS))
    for a in range(0, n, 2000):
        C = ctr[idx[a:a + 2000]].astype(np.float32); s1 += C.sum(0); X = C.reshape(-1, CHN, M * M, F)
        for ch in range(CHN):
            for c in range(M * M): same[ch, c] += X[:, ch, c, :].T @ X[:, ch, c, :]
        for q in range(len(SPN)):
            ok = nbidx[q] >= 0; spat[q, ok] += (C[:, ok] * C[:, nbidx[q][ok]]).sum(0)
    return n, s1, same, spat
def mi(n, pi, pj, n11):
    p11 = n11 / n; p10 = pi - p11; p01 = pj - p11; p00 = 1 - pi - pj + p11; e = 1e-9; r = 0
    for pab, pa, pb in ((p11, pi, pj), (p10, pi, 1 - pj), (p01, 1 - pi, pj), (p00, 1 - pi, 1 - pj)): r = r + np.maximum(pab, e) * np.log(np.maximum(pab, e) / (np.maximum(pa, e) * np.maximum(pb, e)))
    return r
def select(st):
    n, s1, same, spat = st; p = s1 / n; cand = np.full((NBITS, F + len(SPN)), -1, np.int64); score = np.full((NBITS, F + len(SPN)), -np.inf)
    for ch in range(CHN):
        for c in range(M * M):
            base = ch * M * M * F + c * F; pi = p[base:base + F]; M_ = mi(n, pi[:, None], pi[None, :], same[ch, c]); np.fill_diagonal(M_, -np.inf)
            for f in range(F): cand[base + f, :F] = base + np.arange(F); score[base + f, :F] = M_[f]
    for q in range(len(SPN)):
        ok = nbidx[q] >= 0; v = np.full(NBITS, -np.inf); v[ok] = mi(n, p[ok], p[nbidx[q][ok]], spat[q][ok]); cand[:, F + q] = nbidx[q]; score[:, F + q] = v
    top = np.argsort(-score, 1)[:, :K]; return np.take_along_axis(cand, top, 1)
def fixed():
    par = np.zeros((NBITS, K), np.int64)
    for k in range(K): par[:, k] = np.where(nbidx[k] >= 0, nbidx[k], np.arange(NBITS))
    return par
def ctx(C, par): return (C[:, par].astype(np.int64) << np.arange(K)[None, None, :]).sum(2)
base = (np.arange(NBITS) * NCTX)[None, :]
def fit(par_c):
    lt = np.zeros((10, NBITS * NCTX), np.float32); l1 = np.zeros_like(lt)
    for c in range(10):
        idc = np.where(ytr[:ntr] == c)[0]; n = np.zeros(NBITS * NCTX); s = np.zeros(NBITS * NCTX)
        for a in range(0, len(idc), 1000):
            Cc = ctr[idc[a:a + 1000]]; ix = (base + ctx(Cc, par_c[c])).ravel(); n += np.bincount(ix, minlength=NBITS * NCTX); s += np.bincount(ix, weights=Cc.ravel(), minlength=NBITS * NCTX)
        t = (s + 0.5) / (n + 1.0); lt[c] = np.log(t); l1[c] = np.log(1 - t)
    return lt, l1
def score(par_c, lt, l1, C=cte):
    out = np.zeros((len(C), 10), np.float32)
    for a in range(0, len(C), 1000):
        Ci = C[a:a + 1000]; Cf = Ci.astype(np.float32); shared = all(par_c[c] is par_c[0] for c in range(10)); ix0 = base + ctx(Ci, par_c[0]) if shared else None
        for c in range(10):
            ix = ix0 if shared else base + ctx(Ci, par_c[c]); out[a:a + 1000, c] = (Cf * lt[c][ix] + (1 - Cf) * l1[c][ix]).sum(1)
    return out
fx = fixed(); pooled = select(stats(np.arange(ntr))); print("[%4.0fs] pooled wiring chosen" % (time.time() - t0), flush=True)
classwise = []
for c in range(10): classwise.append(select(stats(np.where(ytr[:ntr] == c)[0])))
print("[%4.0fs] class-specific wiring chosen" % (time.time() - t0), flush=True)
for name, pc in (("A fixed spatial parents", [fx] * 10), ("B information-chosen parents, pooled data", [pooled] * 10), ("C information-chosen parents, per class", classwise)):
    lt, l1 = fit(pc); sc = score(pc, lt, l1); print("[%4.0fs] " % (time.time() - t0), end=""); report(name, sc)
same = [np.array_equal(classwise[a], classwise[b]) for a in range(10) for b in range(a + 1, 10)]
print("share of bits whose parents differ between Shirt (6) and T-shirt (0): %.3f" % (classwise[6] != classwise[0]).any(1).mean())
