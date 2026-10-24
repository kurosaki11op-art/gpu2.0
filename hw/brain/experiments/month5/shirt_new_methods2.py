"""24 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. Method 3: nearest-exemplar (popcount) second opinion on the four confusable classes (upper bound for a local, nonlinear readout; memory is large). Method 5: sub-class tables (each cluster class split into K styles by k-means on the code, one table row per style, class score = max over its styles)."""
from shirt_new_methods_setup import *
import sys
K = int(sys.argv[1]) if len(sys.argv) > 1 else 3
W0 = train_table(ctr, ytr); base = cte.astype(np.int32) @ W0; report("baseline L (single view)", base)
Xc = cte.astype(np.float32)
# M3: kNN over cluster training images
sel = np.where(np.isin(ytr, CL))[0]; Tc = ctr[sel].astype(np.float32); yc = ytr[sel]
sim = np.zeros((len(cte), 4), np.float32)
for i in range(0, len(cte), 2000):
    s = Xc[i:i + 2000] @ Tc.T                                  # shared active bits = popcount of AND
    nrm = np.sqrt(Tc.sum(1))[None, :] * np.sqrt(Xc[i:i + 2000].sum(1))[:, None] + 1e-6; s = s / nrm
    for j, c in enumerate(CL):
        sc = s[:, yc == c]; sim[i:i + 2000, j] = np.sort(sc, 1)[:, -10:].mean(1)
print("kNN done", flush=True)
for a in (0.0, 1.0, 3.0, 10.0):
    sc = base.astype(np.float32).copy(); z = base.std()
    sc[:, CL] += a * z * (sim - sim.mean(1, keepdims=True)) / (sim.std() + 1e-6)
    report("M3 table + kNN second opinion weight %.0f" % a, sc)
mk = np.isin(yte, CL); print("M3 kNN alone on cluster: %.4f" % (CL[sim[mk].argmax(1)] == yte[mk]).mean(), flush=True)
# M5: sub-class tables
rs = np.random.RandomState(0); lab = ytr.copy(); nxt = 10; owner = list(range(10))
for c in CL:
    idx = np.where(ytr == c)[0]; X = ctr[idx].astype(np.float32); cen = X[rs.choice(len(X), K, replace=False)]
    for _ in range(8):
        a = ((X @ cen.T) / np.sqrt(cen.sum(1))[None] ).argmax(1)
        cen = np.stack([X[a == k].mean(0) if (a == k).any() else cen[k] for k in range(K)])
    for k in range(1, K):
        lab[idx[a == k]] = nxt; owner.append(c); nxt += 1
    print("class %s sub-class sizes %s" % (NAMES[c], np.bincount(a, minlength=K)), flush=True)
m = CortexSlow(ctr.shape[1], n_cls=nxt, ch=500, K=5, night_stop=2, daydream=1, seed=1); o = np.random.RandomState(100).permutation(len(lab)); m.stage(ctr[o], lab[o])
S = cte.astype(np.int32) @ m.S.T.astype(np.int32); owner = np.array(owner); sc = np.full((len(cte), 10), -(1 << 30), np.int64)
for j in range(nxt): sc[:, owner[j]] = np.maximum(sc[:, owner[j]], S[:, j])
report("M5 sub-class tables K=%d (%d rows)" % (K, nxt), sc)
