"""25 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. L-Genome kill test 3: hierarchy (parents from coarser layers).
Derived coarser layers, built by OR over detectors that fired (no learning): level 2 = each detector fired anywhere in the 2x2-cell block (4 channels x 3x3 blocks x 32 = 1,152 bits); level 3 = each detector fired anywhere in the image (4 x 32 = 128 bits).
Each of the 4,608 detector bits chooses K=3 parents, by counted mutual information, among: same-cell partners (31), spatial neighbours (4), the 32 level-2 bits of its block, the 32 level-3 bits of its channel. Compared with the flat choice (same-cell and spatial only) at the same table budget (8 contexts per bit per class).
 H0 flat, parents chosen on pooled data (= B in genome_test1)   H1 hierarchical, pooled   H2 hierarchical, per class
env: K (parents, default 3)"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, report, CL
K = int(os.environ.get("K", 3)); NCTX = 1 << K; CHN, M, F = 4, 6, 32; NBITS = CHN * M * M * F; ntr = 50000; t0 = time.time()
SPN = [(0, -1), (-1, 0), (-1, -1), (-1, 1)]; NC2 = CHN * 9 * F; NG = CHN * F; NEXT = NBITS + NC2 + NG
def extend(C):
    out = np.zeros((len(C), NEXT), np.uint8); out[:, :NBITS] = C; X = C.reshape(-1, CHN, 3, 2, 3, 2, F) if False else C.reshape(-1, CHN, M, M, F)
    c2 = X.reshape(-1, CHN, 3, 2, 3, 2, F).max(axis=(3, 5)); out[:, NBITS:NBITS + NC2] = c2.reshape(len(C), -1); out[:, NBITS + NC2:] = X.max(axis=(2, 3)).reshape(len(C), -1); return out
def bit(ch, i, j, f): return ch * M * M * F + (i * M + j) * F + f
def c2bit(ch, ci, cj, g): return NBITS + ch * 9 * F + (ci * 3 + cj) * F + g
def gbit(ch, g): return NBITS + NC2 + ch * F + g
nbidx = np.full((len(SPN), NBITS), -1, np.int64)
for ch in range(CHN):
    for i in range(M):
        for j in range(M):
            for f in range(F):
                for q, (di, dj) in enumerate(SPN):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < M and 0 <= jj < M: nbidx[q, bit(ch, i, j, f)] = bit(ch, ii, jj, f)
def stats(idx):
    n = len(idx); s1 = np.zeros(NEXT); same = np.zeros((CHN, M * M, F, F)); cross2 = np.zeros((CHN, M * M, F, F)); glob = np.zeros((CHN, M * M, F, F)); spat = np.zeros((len(SPN), NBITS))
    for a in range(0, n, 2000):
        Ce = extend(ctr[idx[a:a + 2000]]); C = Ce[:, :NBITS].astype(np.float32); s1 += Ce.sum(0); X = C.reshape(-1, CHN, M * M, F)
        C2 = Ce[:, NBITS:NBITS + NC2].astype(np.float32).reshape(-1, CHN, 9, F); Gl = Ce[:, NBITS + NC2:].astype(np.float32).reshape(-1, CHN, F)
        for ch in range(CHN):
            for c in range(M * M):
                i, j = divmod(c, M); cc = (i // 2) * 3 + (j // 2); A = X[:, ch, c, :]
                same[ch, c] += A.T @ A; cross2[ch, c] += A.T @ C2[:, ch, cc, :]; glob[ch, c] += A.T @ Gl[:, ch, :]
        for q in range(len(SPN)):
            ok = nbidx[q] >= 0; spat[q, ok] += (C[:, ok] * C[:, nbidx[q][ok]]).sum(0)
    return n, s1, same, cross2, glob, spat
def mi(n, pi, pj, n11):
    p11 = n11 / n; p10 = pi - p11; p01 = pj - p11; p00 = 1 - pi - pj + p11; e = 1e-9; r = 0
    for pab, pa, pb in ((p11, pi, pj), (p10, pi, 1 - pj), (p01, 1 - pi, pj), (p00, 1 - pi, 1 - pj)): r = r + np.maximum(pab, e) * np.log(np.maximum(pab, e) / (np.maximum(pa, e) * np.maximum(pb, e)))
    return r
def select(st, hier):
    n, s1, same, cross2, glob, spat = st; p = s1 / n; W = F + len(SPN) + (2 * F if hier else 0); cand = np.full((NBITS, W), -1, np.int64); score = np.full((NBITS, W), -np.inf)
    for ch in range(CHN):
        for c in range(M * M):
            i, j = divmod(c, M); cc = (i // 2) * 3 + (j // 2); base = bit(ch, i, j, 0); pi = p[base:base + F]
            Ms = mi(n, pi[:, None], pi[None, :], same[ch, c]); np.fill_diagonal(Ms, -np.inf)
            for f in range(F): cand[base + f, :F] = base + np.arange(F); score[base + f, :F] = Ms[f]
            if hier:
                pc = p[c2bit(ch, i // 2, j // 2, 0):c2bit(ch, i // 2, j // 2, 0) + F]; pg = p[gbit(ch, 0):gbit(ch, 0) + F]
                M2 = mi(n, pi[:, None], pc[None, :], cross2[ch, c]); Mg = mi(n, pi[:, None], pg[None, :], glob[ch, c])
                for f in range(F):
                    cand[base + f, F + 4:F + 4 + F] = c2bit(ch, i // 2, j // 2, 0) + np.arange(F); score[base + f, F + 4:F + 4 + F] = M2[f]
                    cand[base + f, F + 4 + F:] = gbit(ch, 0) + np.arange(F); score[base + f, F + 4 + F:] = Mg[f]
    for q in range(len(SPN)):
        ok = nbidx[q] >= 0; v = np.full(NBITS, -np.inf); v[ok] = mi(n, p[:NBITS][ok], p[:NBITS][nbidx[q][ok]], spat[q][ok]); cand[:, F + q] = nbidx[q]; score[:, F + q] = v
    top = np.argsort(-score, 1)[:, :K]; par = np.take_along_axis(cand, top, 1); return par
def ctx(Ce, par): return (Ce[:, par].astype(np.int64) << np.arange(K)[None, None, :]).sum(2)
base = (np.arange(NBITS) * NCTX)[None, :]
def fit(par_c):
    lt = np.zeros((10, NBITS * NCTX), np.float32); l1 = np.zeros_like(lt)
    for c in range(10):
        idc = np.where(ytr[:ntr] == c)[0]; n = np.zeros(NBITS * NCTX); s = np.zeros(NBITS * NCTX)
        for a in range(0, len(idc), 1000):
            Ce = extend(ctr[idc[a:a + 1000]]); ix = (base + ctx(Ce, par_c[c])).ravel(); n += np.bincount(ix, minlength=NBITS * NCTX); s += np.bincount(ix, weights=Ce[:, :NBITS].ravel(), minlength=NBITS * NCTX)
        t = (s + 0.5) / (n + 1.0); lt[c] = np.log(t); l1[c] = np.log(1 - t)
    return lt, l1
def score_all(par_c, lt, l1, C=cte):
    out = np.zeros((len(C), 10), np.float32); shared = all(par_c[c] is par_c[0] for c in range(10))
    for a in range(0, len(C), 1000):
        Ce = extend(C[a:a + 1000]); Cf = Ce[:, :NBITS].astype(np.float32); ix0 = base + ctx(Ce, par_c[0]) if shared else None
        for c in range(10):
            ix = ix0 if shared else base + ctx(Ce, par_c[c]); out[a:a + 1000, c] = (Cf * lt[c][ix] + (1 - Cf) * l1[c][ix]).sum(1)
    return out
st_all = stats(np.arange(ntr)); print("[%4.0fs] pooled statistics" % (time.time() - t0), flush=True)
p_flat = select(st_all, False); p_hier = select(st_all, True)
hier_share = ((p_hier >= NBITS).mean()); print("share of chosen parents that come from a coarser layer (pooled): %.3f" % hier_share, flush=True)
cls_hier = [select(stats(np.where(ytr[:ntr] == c)[0]), True) for c in range(10)]; print("[%4.0fs] class-specific hierarchical wiring chosen" % (time.time() - t0), flush=True)
for name, pc in (("H0 flat parents, pooled", [p_flat] * 10), ("H1 hierarchical parents, pooled", [p_hier] * 10), ("H2 hierarchical parents, per class", cls_hier)):
    lt, l1 = fit(pc); sc = score_all(pc, lt, l1); print("[%4.0fs] " % (time.time() - t0), end=""); report(name, sc)
