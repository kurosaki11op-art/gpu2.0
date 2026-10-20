"""Reward-gated detector learning (20 Oct 2026), SIMULATED. Brain counterpart of task-driven features: a local three-factor rule. After the table has learned, a training image it gets wrong (the surprise / dopamine signal) points at its most misleading active bit,
the one whose table entry favours the rival over the right class most (integer subtraction of two table entries); the patch behind that bit (spot, detector) is a patch the code represents ambiguously. The patches collected this way (most frequent first) are recruited as new detectors
in place of the least-used ones (a detector that rarely wins is recycled, as in the existing reseed). Then the code is recomputed and the table relearned. No labels reach the detectors except through the surprise at the table; no multiplies, no backprop.
Evaluation each round: the chip's own table (one pass, margin 256 / 1,500 dreams / 1 night) and the float ridge ceiling. usage: DATA_DIR; env DS, NPS, ROUNDS, M (recruits per channel per round), MODE replace|grow."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import detector_learn, feature_layer
from feature_layer import patches, binarize, support_filter
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); NPS = int(os.environ.get("NPS", 2000)); ROUNDS = int(os.environ.get("ROUNDS", 4)); M = int(os.environ.get("M", 6)); MODE = os.environ.get("MODE", "replace"); NERR = int(os.environ.get("NERR", 1500))
STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]; Y = np.eye(10, dtype=np.float32)[ytr]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); F = fes[0].F; m = 6
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
CFG = dict(margin=256, ndream=1500, night=1)


def ridge(ctr, cte):
    ctr = ctr.astype(np.float32); cte = cte.astype(np.float32); mu = ctr.mean(0); A = ctr - mu; Kt = A @ A.T; Kte = (cte - mu) @ A.T; best = 0
    for lam in (100.0, 300.0, 1000.0):
        al = np.linalg.solve(Kt + lam * np.eye(len(Kt), dtype=np.float32), Y - Y.mean(0)); best = max(best, float(((Kte @ al).argmax(1) == yte).mean()))
    return best


def chip_once(ctr, cte, seed=1, staged=False):
    c = CortexSlow(ctr.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed, **CFG)
    for i, s in enumerate(STAGES if staged else [tuple(range(10))]):
        o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; c.stage(ctr[o], ytr[o])
    return c, float((c.predict(cte) == yte).mean())


def evaluate(tag, staged=False):
    ctr, cte = enc(xtr), enc(xte); c, a = chip_once(ctr, cte); r = ridge(ctr, cte); s = chip_once(ctr, cte, staged=True)[1] if staged else float("nan")
    print(DS, tag, "bits", ctr.shape[1], "chip one-pass %.4f" % a, "ridge %.4f" % r, "chip staged %.4f" % s, "%.0fs" % (time.time() - t0), flush=True); return ctr, c


ctr, c = evaluate("round 0 (shipped)", staged=True)
for rd in range(1, ROUNDS + 1):
    W = c.W.astype(np.int32); pred = (ctr.astype(np.int32) @ W.T).argmax(1); err = np.where(pred != ytr)[0]; err = err[np.random.RandomState(rd).permutation(len(err))[:NERR]]
    cand = [dict() for _ in fes]                                            # per channel: patch bytes -> [count, patch]
    for i in err:
        y, rv = ytr[i], pred[i]; act = np.where(ctr[i])[0]; d = W[rv, act] - W[y, act]; b = act[d.argmax()]
        ch, rem = divmod(int(b), m * m * F); cell, f = divmod(rem, F); ci, cj = divmod(cell, m); g = fes[ch]
        p, n = patches(support_filter(binarize(xtr[i:i + 1], g.thr), g.support)); t = np.where(g.cnt >= 0, 1, -1); w = (np.where(p[0], 1, -1) @ t.T).argmax(1)
        for di in range(g.pool):
            for dj in range(g.pool):
                s = (g.pool * ci + di) * n + (g.pool * cj + dj)
                if w[s] == f and p[0, s].sum() >= g.min_on:
                    k = p[0, s].tobytes(); cand[ch].setdefault(k, [0, p[0, s]])[0] += 1; break
            else: continue
            break
    for ch, g in enumerate(fes):
        top = sorted(cand[ch].values(), key=lambda v: -v[0])[:M]
        if MODE == "grow":
            g.cnt = np.concatenate([g.cnt, np.where(np.stack([v[1] for v in top]), 1, -1).astype(np.int32)]) if top else g.cnt; g.F = len(g.cnt)
        else:
            used = np.zeros(g.F, int); xs = xtr[:1500]; pp, n = patches(support_filter(binarize(xs, g.thr), g.support)); wn = (np.where(pp.reshape(-1, pp.shape[-1]), 1, -1) @ np.where(g.cnt >= 0, 1, -1).T).argmax(1); used = np.bincount(wn, minlength=g.F)
            for slot, v in zip(np.argsort(used)[:len(top)], top): g.cnt[slot] = np.where(v[1], 1, -1)
    F = fes[0].F
    ctr, c = evaluate("round %d (%s, %d recruits/channel, %d errors used)" % (rd, MODE, M, len(err)), staged=(rd == ROUNDS))
