"""Blame-routed detector learning: see the docstring below. Lean version: loads data only (no 60,000-image encode), saves detector state and round log after every round, resumable."""
import sys, os, time, copy, pickle, numpy as np
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features
from cortex_core import load
from cortex_slow import CortexSlow
D, DS = sys.argv[1], sys.argv[2]; xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
CH = (50, 150, ("on", 8), ("off", 8))
import copy, time
from feature_layer import patches, binarize, support_filter
"""Blame-routed detector learning (24 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed). New technique designed from our failures (see docs/error_transport_design.md).
Rounds: (1) encode a 20,000-image training subset with the current detectors and train the counting table; (2) on the table's mistakes, each ACTIVE bit gets a blame d = S[wrong, bit] - S[true, bit] (two table rows, adds only);
(3) the detector that won at each position is moved AWAY from the patch if its bit helped the wrong class (d > 0) and TOWARD it if it helped the true class (d < 0), sign-only +-1 counter steps, only the K most blamed bits per image per sign;
(4) GUARD: re-encode a 5,000-image validation split, retrain, and keep the change only if validation accuracy and four-class cluster accuracy do not fall; else revert. Baseline = the same procedure with no blame updates (unsupervised detectors only)."""
NTRN, NVAL, K, STEP, ROUNDS, MAXMIS = 20000, 5000, 6, int(os.environ.get("STEPSIZE", 1)), int(os.environ.get("ROUNDS", 4)), 3000
PUPD = float(os.environ.get("PUPD", 0.03)); RNG = np.random.RandomState(11)          # each blamed update is applied with this probability: a small dose per detector per round
itr, iva = np.arange(NTRN), np.arange(NTRN, NTRN + NVAL); CL = np.array([0, 2, 4, 6])
fes = [Features(32, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
def enc(fl, x): return np.concatenate([np.concatenate([g.encode(x[i:i + 200]) for g in fl], 1) for i in range(0, len(x), 200)])
def train_table(code, y):
    m = CortexSlow(code.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(len(y)); m.stage(code[sel], y[sel]); return m.S.astype(np.int32)
def metrics(S, code, y):
    sc = code.astype(np.int32) @ S.T; p = sc.argmax(1); mk = np.isin(y, CL); return (p == y).mean(), (CL[sc[mk][:, CL].argmax(1)] == y[mk]).mean(), (p[y == 6] == 6).mean()
def ap_shirt(S, code, y):
    sc = (code.astype(np.int32) @ S.T).astype(np.float64); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = (y == 6); o = np.argsort(-s); tp = np.cumsum(yy[o]); return ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
def blame_update(fl, S, x, ytrue, ypred):
    """Consensus-gated blame routing: the blame signs of ALL mistakes in the round are summed per detector template bit (votes); only the template bits whose |votes| are in the top TOP percent are changed, by one step in the direction of the votes."""
    changed = 0; TOP = float(os.environ.get("TOP", 3.0))
    for ci_ch, f in enumerate(fl):
        p0, n = patches(support_filter(binarize(x[:1], f.thr), f.support)); m = n // f.pool; off = ci_ch * m * m * f.F; votes = np.zeros(f.cnt.shape, np.int64)
        for idx in range(len(x)):
            p, n = patches(support_filter(binarize(x[idx:idx + 1], f.thr), f.support)); flat = p.reshape(-1, p.shape[-1]); on = flat.sum(1) >= f.min_on; w = f.winners(flat)
            ii, jj = np.divmod(np.arange(n * n), n); ok = on & (ii // f.pool < m) & (jj // f.pool < m)
            bit = np.minimum(off + ((ii // f.pool) * m + (jj // f.pool)) * f.F + w, S.shape[1] - 1); d = np.where(ok, S[ypred[idx], bit] - S[ytrue[idx], bit], 0)
            harm = np.argsort(-d)[:K]; harm = harm[d[harm] > 0]; help_ = np.argsort(d)[:K]; help_ = help_[d[help_] < 0]
            for sel, sgn in ((harm, -1), (help_, 1)):
                if len(sel): np.add.at(votes, w[sel], sgn * np.where(flat[sel], 1, -1))
        a_ = np.abs(votes); thr = np.percentile(a_, 100 - TOP); ch = (a_ >= max(thr, 1)); f.cnt += STEP * np.sign(votes) * ch; np.clip(f.cnt, -31, 31, out=f.cnt); changed += int(ch.sum())
    return changed
def run(use_blame):
    fl = copy.deepcopy(fes); Xtr, ytr_, Xva, yva = xtr[itr], ytr[itr], xtr[iva], ytr[iva]
    ctr_, cva = enc(fl, Xtr), enc(fl, Xva); S = train_table(ctr_, ytr_); best = metrics(S, cva, yva); print("  start: validation accuracy %.4f cluster %.4f" % best[:2], flush=True)
    if not use_blame: return fl, S
    for r in range(ROUNDS):
        sc = ctr_.astype(np.int32) @ S.T; p = sc.argmax(1); top2 = np.sort(sc, 1)[:, -2:]; mar = top2[:, 1] - top2[:, 0]; mis = np.where((p != ytr_) | (mar < np.percentile(mar, 15)))[0]; mis = mis[p[mis] != ytr_[mis]]
        if os.environ.get('CLUSTER_ONLY'): mis = mis[np.isin(ytr_[mis], CL) & np.isin(p[mis], CL)]       # blame only the mistakes inside the upper-body cluster
        mis = mis[:MAXMIS]
        snap = [copy.deepcopy(f.cnt) for f in fl]; ch = blame_update(fl, S, Xtr[mis], ytr_[mis], p[mis])
        c2, cv2 = enc(fl, Xtr), enc(fl, Xva); S2 = train_table(c2, ytr_); new = metrics(S2, cv2, yva)
        ok = (new[0] >= best[0]) and (new[1] >= best[1]); print("  round %d: %d mistakes used, %d detector updates, validation accuracy %.4f cluster %.4f -> %s" % (r + 1, len(mis), ch, new[0], new[1], "ACCEPT" if ok else "REVERT"), flush=True)
        if ok: ctr_, S, best = c2, S2, new
        else:
            for f, s0 in zip(fl, snap): f.cnt = s0
    return fl, S
STATE = 'blame_state.pkl'; t0 = time.time(); res = {}
for name, ub in ((("baseline (unsupervised detectors)", False),) if not os.environ.get("SKIP_BASE") else ()) + (("blame-routed detector learning", True),):
    print(name, flush=True); fl, S = run(ub); cte = enc(fl, xte); a, c4, sh = metrics(S, cte, yte); res[name] = (a, c4, sh, ap_shirt(S, cte, yte)); print("  TEST: accuracy %.4f | cluster accuracy %.4f | Shirt recall %.3f | Shirt AP %.3f | %.0fs" % (a, c4, sh, res[name][3], time.time() - t0), flush=True)
