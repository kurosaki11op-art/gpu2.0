"""25 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. Sleep test of the 'never forgets' design: can L's discriminative counting table be REBUILT from the stable store alone, with no real images?
Stable store = per-class connected counting models over L's 4,608 detector bits (each bit given K=3 earlier bits chosen by counted information; trained on the first 50,000 training images, class by class). Dreams are drawn by ancestral sampling from these tables only (bit by bit in index order, each bit given its sampled parents). The counting table is then trained on dreams only and tested on the real test images.
env: K (parents, default 3), NDREAM (dreams per class, default 6000)"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, report, CL
K = int(os.environ.get("K", 3)); NCTX = 1 << K; NDREAM = int(os.environ.get("NDREAM", 6000)); CHN, M, F = 4, 6, 32; NBITS = CHN * M * M * F; ntr = 50000; t0 = time.time(); rs = np.random.RandomState(0)
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
def mi(n, pi, pj, n11):
    p11 = n11 / n; p10 = pi - p11; p01 = pj - p11; p00 = 1 - pi - pj + p11; e = 1e-9; r = 0
    for pab, pa, pb in ((p11, pi, pj), (p10, pi, 1 - pj), (p01, 1 - pi, pj), (p00, 1 - pi, 1 - pj)): r = r + np.maximum(pab, e) * np.log(np.maximum(pab, e) / (np.maximum(pa, e) * np.maximum(pb, e)))
    return r
idx = np.arange(ntr); n = ntr; s1 = np.zeros(NBITS); same = np.zeros((CHN, M * M, F, F)); spat = np.zeros((len(SPN), NBITS))
for a in range(0, ntr, 2000):
    C = ctr[idx[a:a + 2000]].astype(np.float32); s1 += C.sum(0); X = C.reshape(-1, CHN, M * M, F)
    for ch in range(CHN):
        for c in range(M * M): same[ch, c] += X[:, ch, c, :].T @ X[:, ch, c, :]
    for q in range(len(SPN)):
        ok = nbidx[q] >= 0; spat[q, ok] += (C[:, ok] * C[:, nbidx[q][ok]]).sum(0)
p = s1 / n; cand = np.full((NBITS, F + len(SPN)), -1, np.int64); score = np.full((NBITS, F + len(SPN)), -np.inf)
for ch in range(CHN):
    for c in range(M * M):
        base = ch * M * M * F + c * F; pi = p[base:base + F]; Ms = mi(n, pi[:, None], pi[None, :], same[ch, c])
        mask = np.arange(F)[None, :] < np.arange(F)[:, None]                                  # only earlier detectors (smaller index) in the same cell may be parents, so sampling order exists
        Ms = np.where(mask, Ms, -np.inf)
        for f in range(F): cand[base + f, :F] = base + np.arange(F); score[base + f, :F] = Ms[f]
for q in range(len(SPN)):
    ok = nbidx[q] >= 0; v = np.full(NBITS, -np.inf); v[ok] = mi(n, p[ok], p[nbidx[q][ok]], spat[q][ok]); cand[:, F + q] = nbidx[q]; score[:, F + q] = v
top = np.argsort(-score, 1)[:, :K]; par = np.take_along_axis(cand, top, 1); par = np.where(np.take_along_axis(score, top, 1) > -np.inf, par, -1)
print("[%4.0fs] causal wiring chosen (bits with fewer than %d parents: %d)" % (time.time() - t0, K, int((par < 0).any(1).sum())), flush=True)
valid = par >= 0; parc = np.where(valid, par, 0); wts = (1 << np.arange(K))[None, :]; base = (np.arange(NBITS) * NCTX)[None, :]
def ctx_of(C): return ((C[:, parc].astype(np.int64) * valid[None]) * wts[None]).sum(2)
T = np.zeros((10, NBITS * NCTX), np.float32)
for c in range(10):
    idc = np.where(ytr[:ntr] == c)[0]; nn = np.zeros(NBITS * NCTX); ss = np.zeros(NBITS * NCTX)
    for a in range(0, len(idc), 1000):
        Cc = ctr[idc[a:a + 1000]]; ix = (base + ctx_of(Cc)).ravel(); nn += np.bincount(ix, minlength=NBITS * NCTX); ss += np.bincount(ix, weights=Cc.ravel(), minlength=NBITS * NCTX)
    T[c] = (ss + 0.5) / (nn + 1.0)
print("[%4.0fs] stable store fitted (10 classes)" % (time.time() - t0), flush=True)
D = np.zeros((10 * NDREAM, NBITS), np.uint8); lab = np.repeat(np.arange(10), NDREAM)
for b in range(NBITS):
    ctx = (D[:, parc[b]].astype(np.int64) * valid[b][None] * wts[0][None]).sum(1); pr = T[lab, b * NCTX + ctx]; D[:, b] = rs.rand(len(lab)) < pr
print("[%4.0fs] dreamt %d images: active bits per dream %.0f (real images %.0f)" % (time.time() - t0, len(D), D.sum(1).mean(), ctr[:2000].sum(1).mean()), flush=True)
W = train_table(D, lab); print("[%4.0fs] " % (time.time() - t0), end=""); report("table trained on dreams only (%d per class)" % NDREAM, cte.astype(np.int32) @ W)
W2 = train_table(ctr[:ntr], ytr[:ntr]); print("[%4.0fs] " % (time.time() - t0), end=""); report("reference: table trained on 50,000 real images", cte.astype(np.int32) @ W2)
# generative store read directly (no sleep): log-likelihood classification
lt = np.log(T); l1 = np.log(1 - T); out = np.zeros((len(cte), 10), np.float32)
for a in range(0, len(cte), 1000):
    Ci = cte[a:a + 1000]; ix = base + ctx_of(Ci); Cf = Ci.astype(np.float32)
    for c in range(10): out[a:a + 1000, c] = (Cf * lt[c][ix] + (1 - Cf) * l1[c][ix]).sum(1)
print("[%4.0fs] " % (time.time() - t0), end=""); report("stable store read directly (likelihood)", out)
