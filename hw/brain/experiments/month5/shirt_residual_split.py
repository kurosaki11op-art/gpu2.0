"""25 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. Two label-free ways to add DIFFERENCE information to L's 4,608-bit code (labels are used only by the counting table, as always).
Idea 1, residual layer: K unsupervised prototypes (k-means on codes, bit-rate vectors). Each image is coded by what its nearest prototype does not explain: bits it has that the prototype lacks (r+) and bits the prototype has that it lacks (r-), plus the prototype id.
Idea 2, split where confused: images whose table margin (top1 - top2) is smallest form the ambiguous region; unsupervised k-means inside it; for each pair of sub-clusters, a difference feature = (matches to bits where cluster i is more likely) minus (matches to bits where cluster j is more likely), thresholded into 3 bits. Control: the same procedure on a random region of equal size.
env: K (prototypes, default 64), AMB (fraction of ambiguous images, default 0.2), KS (sub-clusters, default 8), NB (bits per side per pair, default 64)"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, report, CL
E = lambda k, d: type(d)(os.environ.get(k, d))
K, AMB, KS, NB = E("K", 64), E("AMB", 0.2), E("KS", 8), E("NB", 64)
rs = np.random.RandomState(0); t0 = time.time()
def run(tag, Ftr, Fte):
    W = train_table(Ftr, ytr); sc = Fte.astype(np.int32) @ W; print("[%4.0fs] bits %6d active %5.0f | " % (time.time() - t0, Ftr.shape[1], Ftr.sum(1).mean()), end=""); report(tag, sc); return W
def kmeans(X, k, iters=10):
    cen = X[rs.choice(len(X), k, replace=False)].astype(np.float32)
    for _ in range(iters):
        a = ((X @ cen.T) - 0.5 * (cen ** 2).sum(1)[None]).argmax(1)
        cen = np.stack([X[a == j].mean(0) if (a == j).any() else cen[j] for j in range(k)])
    return cen
def assign(X, cen, chunk=5000):
    return np.concatenate([(X[i:i + chunk].astype(np.float32) @ cen.T - 0.5 * (cen ** 2).sum(1)[None]).argmax(1) for i in range(0, len(X), chunk)])
W0 = run("baseline L", ctr, cte)
# ---- Idea 1: residual layer
sub = rs.choice(len(ctr), 20000, replace=False); cen = kmeans(ctr[sub].astype(np.float32), K); Pb = (cen > 0.4).astype(np.uint8)
def resid(C):
    a = assign(C, cen); P = Pb[a]; rp = (C & (1 - P)).astype(np.uint8); rm = ((1 - C) & P).astype(np.uint8); oh = np.eye(K, dtype=np.uint8)[a]; return rp, rm, oh
rp, rm, oh = resid(ctr); rpt, rmt, oht = resid(cte)
print("prototype residual sizes: r+ %.0f bits, r- %.0f bits on average (image has %.0f)" % (rp.sum(1).mean(), rm.sum(1).mean(), ctr.sum(1).mean()), flush=True)
run("1a residual only (r+, r-, prototype id)", np.concatenate([rp, rm, oh], 1), np.concatenate([rpt, rmt, oht], 1))
del rp, rm, rpt, rmt
run("1b L code + prototype id only", np.concatenate([ctr, oh], 1), np.concatenate([cte, oht], 1))
# ---- Idea 2: split where confused
sc0 = ctr[:30000].astype(np.int32) @ W0; srt = np.sort(sc0, 1); marg = srt[:, -1] - srt[:, -2]
def split(region_idx, tag):
    R = ctr[region_idx].astype(np.float32); cs = kmeans(R, KS); rates = cs; feats = []
    for i in range(KS):
        for j in range(i + 1, KS):
            d = rates[i] - rates[j]; pos = np.argsort(-d)[:NB]; neg = np.argsort(d)[:NB]; feats.append((pos, neg))
    def f(C):
        out = []
        for pos, neg in feats:
            s = C[:, pos].sum(1).astype(np.int32) - C[:, neg].sum(1).astype(np.int32); out += [s > 0, s > 6, s < -6]
        return np.stack(out, 1).astype(np.uint8)
    return f(ctr), f(cte)
amb = np.argsort(marg)[:int(AMB * 30000)]; ftr, fte = split(amb, "ambiguous")
run("2a L code + split features (ambiguous region)", np.concatenate([ctr, ftr], 1), np.concatenate([cte, fte], 1))
ctrl = rs.choice(30000, len(amb), replace=False); gtr, gte = split(ctrl, "random")
run("2b control: split features, random region", np.concatenate([ctr, gtr], 1), np.concatenate([cte, gte], 1))
