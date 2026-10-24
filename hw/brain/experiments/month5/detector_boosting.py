"""Error-targeted detector boosting (24 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed). Mechanism designed from the failure of blame-routed template moves: the error acts where the discrete choice is made, on WHICH detectors exist.
Each round: train the counting table, find the training images it gets WRONG, fit R new detectors per channel (the same Hebbian rule) on patches of those images only, APPEND their bits (old detectors untouched, so nothing is forgotten), retrain.
Control arm: the same number of new detectors fitted on patches of random training images. Equal code size in both arms. Table trained on 30,000 images, check set = 10,000 other training images (validation), test = 10,000. Win-win = accuracy, cluster accuracy and Shirt AP up and nothing down."""
import sys, os, time, numpy as np
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features, patches, binarize, support_filter
from cortex_core import load
from cortex_slow import CortexSlow
D, DS = sys.argv[1], sys.argv[2]; xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); CL = np.array([0, 2, 4, 6])
NTR, NVAL, R, ROUNDS = 30000, 10000, int(os.environ.get("R", 8)), int(os.environ.get("ROUNDS", 3)); itr = np.arange(NTR); iva = np.arange(NTR, NTR + NVAL); CH = (50, 150, ("on", 8), ("off", 8)); t0 = time.time()
def enc(fl, x): return np.concatenate([np.concatenate([g.encode(x[i:i + 200]) for g in fl], 1) for i in range(0, len(x), 200)])
def fit_patches(f, p, passes=3, cmax=31):
    p = p[p.sum(1) >= f.min_on]; f.cnt = np.where(p[f.r.choice(len(p), f.F)], 1, -1).astype(np.int32)
    for _ in range(passes):
        wins = np.zeros(f.F, int)
        for i in range(0, len(p), 1000):
            b = p[i:i + 1000]; w = f.winners(b); np.add.at(f.cnt, w, np.where(b, 1, -1)); np.clip(f.cnt, -cmax, cmax, out=f.cnt); wins += np.bincount(w, minlength=f.F)
        dead = np.where(wins == 0)[0]; f.cnt[dead] = np.where(p[f.r.choice(len(p), len(dead))], 1, -1)
    return f
def patches_of(thr, x):
    out = []
    for i in range(0, len(x), 500): p, _ = patches(support_filter(binarize(x[i:i + 500], thr), 0)); out.append(p.reshape(-1, p.shape[-1]))
    return np.concatenate(out)
def table(code, y): m = CortexSlow(code.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(len(y)); m.stage(code[sel], y[sel]); return m.S.astype(np.int32)
def metrics(S, code, y):
    sc = code.astype(np.int32) @ S.T; p = sc.argmax(1); mk = np.isin(y, CL); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = y == 6; o = np.argsort(-s); tp = np.cumsum(yy[o])
    return (p == y).mean(), (CL[sc[mk][:, CL].argmax(1)] == y[mk]).mean(), ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum(), (p[y == 6] == 6).mean(), p
rs = np.random.RandomState(7); base = [Features(32, thr=c, pool=4).fit(xtr[itr][rs.choice(NTR, 12000, replace=False)]) for c in CH]
ctr0, cva0, cte0 = enc(base, xtr[itr]), enc(base, xtr[iva]), enc(base, xte); S0 = table(ctr0, ytr[itr]); m0 = metrics(S0, cva0, ytr[iva]); mt0 = metrics(S0, cte0, yte)
print("base (32 per channel, %d bits): validation acc %.4f cluster %.4f AP %.3f | TEST acc %.4f cluster %.4f Shirt AP %.3f recall %.3f | %.0fs" % (ctr0.shape[1], m0[0], m0[1], m0[2], mt0[0], mt0[1], mt0[2], mt0[3], time.time() - t0), flush=True)
for arm in ("boosting (patches of mistakes)", "control (patches of random images)"):
    ctr, cva, cte = ctr0, cva0, cte0; S = S0; p_tr = (ctr0.astype(np.int32) @ S0.T).argmax(1); extra = []
    for r in range(ROUNDS):
        pool = np.where(p_tr != ytr[itr])[0] if arm.startswith("boosting") else np.random.RandomState(r).choice(NTR, 1500, replace=False)
        if len(pool) > 3000: pool = np.random.RandomState(r).choice(pool, 3000, replace=False)
        nf = [fit_patches(Features(R, thr=c, pool=4, seed=10 + r), patches_of(c, xtr[itr][pool])) for c in CH]; extra.append(nf)
        ctr, cva, cte = [np.concatenate([a, enc(nf, x)], 1) for a, x in ((ctr, xtr[itr]), (cva, xtr[iva]), (cte, xte))]; S = table(ctr, ytr[itr]); p_tr = (ctr.astype(np.int32) @ S.T).argmax(1)
        mv = metrics(S, cva, ytr[iva]); mt = metrics(S, cte, yte)
        print("%-36s round %d (+%d bits, total %d): validation acc %.4f cluster %.4f AP %.3f | TEST acc %.4f cluster %.4f Shirt AP %.3f recall %.3f | %.0fs" % (arm, r + 1, R * 144, ctr.shape[1], mv[0], mv[1], mv[2], mt[0], mt[1], mt[2], mt[3], time.time() - t0), flush=True)
