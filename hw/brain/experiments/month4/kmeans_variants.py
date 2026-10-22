"""Integer grouping variants (22 Oct 2026) SIMULATED: which integer rule groups the joined picture + sound codes (10 groups, no labels) as well as the float k-means? Purity on the dumped codes of brain_strict_cocluster.py (seed 1). usage: CODES.npz"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, cross_modal
z = np.load(sys.argv[1]); X = z["joint"].astype(bool); y = z["y"]; K = 10; N = len(X); Xi = X.astype(np.int32)
def purity(a): return float(sum(np.bincount(y[a == j], minlength=10).max() for j in range(K) if (a == j).any()) / len(y))
def float_km(seed, iters=25, restarts=3):
    Xf = X.astype(np.float32); best = (-1e18, None); g = np.random.RandomState(seed)
    for _ in range(restarts):
        c = [Xf[g.randint(N)]]
        for _k in range(1, K):
            d = np.min([((Xf - ci) ** 2).sum(1) for ci in c], 0); c.append(Xf[g.choice(N, p=d / (d.sum() + 1e-9))])
        c = np.stack(c)
        for _i in range(iters):
            sc = Xf @ c.T - 0.5 * (c * c).sum(1)[None, :]; a = sc.argmax(1)
            for j in range(K):
                if (a == j).any(): c[j] = Xf[a == j].mean(0)
        sc = Xf @ c.T - 0.5 * (c * c).sum(1)[None, :]; tot = float(sc.max(1).sum())
        if tot > best[0]: best = (tot, sc.argmax(1))
    return best[1]
def rate_km(init, seed, iters=8, restarts=3, bits=4):
    """prototypes keep rates (member counts per bit quantised to `bits` bits); score = x . r - sum(r^2) / 2^(bits+1) (the k-means distance with quantised means)"""
    g = np.random.RandomState(seed); best = (None, None); Q = (1 << bits) - 1
    for rr in range(restarts):
        if init == "rand": idx = g.choice(N, K, replace=False)
        else:
            idx = [int(g.randint(N))]
            for _ in range(1, K):
                P = X[idx]; s = 2 * (Xi @ P.T.astype(np.int32)) - P.sum(1)[None, :]; idx.append(int(np.argmin(s.max(1))))
        R = (X[idx].astype(np.int32) * Q)
        for _ in range(iters):
            sc = Xi @ R.T - (R.astype(np.int64) ** 2).sum(1)[None, :] // (2 * Q); a = sc.argmax(1)
            for j in range(K):
                m = int((a == j).sum())
                if m: R[j] = (Xi[a == j].sum(0) * Q + m // 2) // m
        sc = Xi @ R.T - (R.astype(np.int64) ** 2).sum(1)[None, :] // (2 * Q); tot = int(sc.max(1).sum())
        if best[0] is None or tot > best[0]: best = (tot, sc.argmax(1))
    return best[1]
t0 = time.time()
print("float k-means (host)      ", "%.3f" % purity(float_km(1)), "%.0fs" % (time.time() - t0), flush=True)
print("integer, current (binary, farthest-first, 3 restarts)", "%.3f" % purity(cross_modal.kmeans_int(X, K, 8, 3)), flush=True)
print("integer, current, 8 iter, 8 restarts", "%.3f" % purity(cross_modal.kmeans_int(X, K, 8, 8)), flush=True)
for init in ("rand", "far"):
    for bits in (2, 4):
        for seed in (1, 2):
            print("rate prototypes (%d-bit), %s init, seed %d: %.3f" % (bits, init, seed, purity(rate_km(init, seed, 8, 3, bits))), flush=True)
