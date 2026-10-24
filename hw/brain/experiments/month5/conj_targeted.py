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

"""Error-targeted conjunction layer (L-native second layer, 24 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed). A unit = AND of two first-layer bits (fires only when both are active: sparse, event-driven, no multiplies), selected BY COUNTING.
Targeted arm: find the table's most frequent confusions on the training set (true class c called w), generate candidate conjunctions from pairs of active bits of the mistaken images, keep per confusion the ones whose firing rate differs most between class c and class w (counts and compares only).
Control arm: the same NUMBER of conjunctions from random active-bit pairs of random images, chosen by global contrast (max over classes of P(fires | class) - P(fires | not class)), as in the earlier test. Equal added bits. Table trained on 30,000 images, validation 10,000 other training images, test 10,000. Win-win = accuracy, cluster accuracy and Shirt AP all up, nothing down."""
NADD = int(os.environ.get("NADD", 6000)); NPAIR = 6; CAND = 40000
rs = np.random.RandomState(7); base = [Features(32, thr=c, pool=4).fit(xtr[itr][rs.choice(NTR, 12000, replace=False)]) for c in CH]
ctr0, cva0, cte0 = [enc(base, x).astype(np.uint8) for x in (xtr[itr], xtr[iva], xte)]; S0 = table(ctr0, ytr[itr]); mv0 = metrics(S0, cva0, ytr[iva]); mt0 = metrics(S0, cte0, yte); y_tr = ytr[itr]
def rep(tag, bits, mv, mt): print("%-40s +%5d bits: validation acc %.4f cluster %.4f AP %.3f | TEST acc %.4f cluster %.4f Shirt AP %.3f recall %.3f | %.0fs" % (tag, bits, mv[0], mv[1], mv[2], mt[0], mt[1], mt[2], mt[3], time.time() - t0), flush=True)
rep("base", 0, mv0, mt0)
def conj(A, pairs): return (A[:, pairs[:, 0]] & A[:, pairs[:, 1]])
def sample_pairs(A, rows, n, rng):                                     # random pairs of ACTIVE bits taken from the given images
    out = []
    while len(out) < n:
        i = rng.choice(rows); act = np.nonzero(A[i])[0]
        if len(act) >= 2: out.append(rng.choice(act, 2, replace=False))
    return np.array(out)
def evaluate(tag, pairs):
    ctr, cva, cte = [np.concatenate([a, conj(a, pairs)], 1) for a in (ctr0, cva0, cte0)]; S = table(ctr, y_tr); rep(tag, len(pairs), metrics(S, cva, ytr[iva]), metrics(S, cte, yte))
# targeted
p_tr = (ctr0.astype(np.int32) @ S0.T).argmax(1); wrong = np.where(p_tr != y_tr)[0]; conf = {}
for i in wrong: k = tuple(sorted((int(y_tr[i]), int(p_tr[i])))); conf[k] = conf.get(k, 0) + 1
top = sorted(conf, key=conf.get, reverse=True)[:NPAIR]; print("most frequent confusions (class pair: count):", {k: conf[k] for k in top}, flush=True)
rng = np.random.RandomState(3); sel = []
for (c, w) in top:
    rows_cw = np.where(np.isin(y_tr, (c, w)))[0]; mis = wrong[np.isin(y_tr[wrong], (c, w)) & np.isin(p_tr[wrong], (c, w))]
    cand = sample_pairs(ctr0, mis, CAND, rng); f = conj(ctr0[rows_cw], cand); yc = (y_tr[rows_cw] == c); pc, pw = f[yc].mean(0), f[~yc].mean(0); diff = pc - pw
    half = NADD // (2 * NPAIR); sel += [cand[j] for j in np.argsort(-diff)[:half]] + [cand[j] for j in np.argsort(diff)[:half]]
evaluate("error-targeted conjunctions", np.array(sel))
# control: global contrast
cand = sample_pairs(ctr0, np.arange(NTR), CAND * 3, np.random.RandomState(5)); f = conj(ctr0[np.random.RandomState(1).choice(NTR, 15000, replace=False)], cand); yy = y_tr[np.random.RandomState(1).choice(NTR, 15000, replace=False)]
best = np.zeros(len(cand))
for c in range(10): best = np.maximum(best, f[yy == c].mean(0) - f[yy != c].mean(0))
evaluate("control: global-contrast conjunctions", cand[np.argsort(-best)[:NADD]])
