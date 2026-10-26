"""26 Oct 2026, SIMULATED, Fashion-MNIST, one seed. Piece 3: never forgetting / never stopping with an append-only clause bank per class (clause learner of tm_faithful.py, 300 clauses per class, inputs = L's detector code + raw-pixel bits).
Stage 1 trains classes 0-5 (jointly). Stage 2 trains ONLY the banks of classes 6-9 and never touches the old banks (append-only, nothing rewritten). Stage 2 sees no old-class images. Negatives for a new bank come from the other new classes' images; MODE=dream adds dreamed images of the old classes (drawn from a stored per-class table of bit frequencies, 6,176 counters per class = counting memory, no images kept).
Reference MODE=joint trains all ten classes together with the same budget. Scores for the decision: unclipped class sums (clause counts), argmax over all ten classes (class-incremental: no task label at test).
env: MODE (joint|none|dream), CC clauses per class, EP epochs per stage."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, xtr, xte
from numba import njit, prange
def bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
X = np.concatenate([ctr, bits(xtr)], 1).astype(np.uint8); Xt = np.concatenate([cte, bits(xte)], 1).astype(np.uint8); y = ytr.astype(np.int64)
NB = X.shape[1]; NL = 2 * NB; C = int(os.environ.get("CC", 300)); T = int(os.environ.get("TT", 25)); S = 3.0; NST = 100; LMAX = 256; MODE = os.environ.get("MODE", "none"); EP = int(os.environ.get("EP", 4)); SEED = int(os.environ.get("SEED", 0))
OLD, NEW = [0, 1, 2, 3, 4, 5], [6, 7, 8, 9]
@njit
def fires(cl, x, inc_list, inc_n):
    n = inc_n[cl]
    if n == 0: return 1
    for t in range(n):
        lit = inc_list[cl, t]
        if lit < NB:
            if x[lit] == 0: return 0
        elif x[lit - NB] == 1: return 0
    return 1
@njit
def class_sum(c, x, inc_list, inc_n, outs, clip):
    v = 0
    for j in range(C):
        o = fires(c * C + j, x, inc_list, inc_n); outs[j] = o
        if o: v += 1 if j % 2 == 0 else -1
    return max(-T, min(T, v)) if clip else v
@njit(parallel=True)
def feedback(c, x, state, inc_list, inc_n, outs, v, positive_target):
    p = (T - v) / (2.0 * T) if positive_target else (T + v) / (2.0 * T)
    for j in prange(C):
        if np.random.random() > p: continue
        cl = c * C + j; type1 = ((j % 2 == 0) == positive_target)
        if type1:
            if outs[j] == 1:
                for k in range(NL):
                    lt = x[k] == 1 if k < NB else x[k - NB] == 0
                    if lt:
                        if np.random.random() < (S - 1.0) / S and state[cl, k] < 2 * NST: state[cl, k] += 1
                    elif np.random.random() < 1.0 / S and state[cl, k] > 1: state[cl, k] -= 1
            else:
                for k in range(NL):
                    if np.random.random() < 1.0 / S and state[cl, k] > 1: state[cl, k] -= 1
        elif outs[j] == 1:
            for k in range(NL):
                lt = x[k] == 1 if k < NB else x[k - NB] == 0
                if (not lt) and state[cl, k] <= NST: state[cl, k] += 1
        n = 0
        for k in range(NL):
            if state[cl, k] > NST and n < LMAX: inc_list[cl, n] = k; n += 1
        inc_n[cl] = n
@njit
def train(Xs, ys, order, classes, rates, dream_p, state, inc_list, inc_n, seed):
    np.random.seed(seed); outs = np.zeros(C, np.int8); outs2 = np.zeros(C, np.int8); nc = len(classes); old_n = rates.shape[0]
    for ii in range(len(order)):
        i = order[ii]; x = Xs[i]; a = ys[i]
        v = class_sum(a, x, inc_list, inc_n, outs, True); feedback(a, x, state, inc_list, inc_n, outs, v, True)
        o = classes[np.random.randint(nc)]
        while o == a: o = classes[np.random.randint(nc)]
        v2 = class_sum(o, x, inc_list, inc_n, outs2, True); feedback(o, x, state, inc_list, inc_n, outs2, v2, False)
        if dream_p > 0 and np.random.random() < dream_p:                                         # negative example drawn from an old class's stored bit frequencies
            oc = np.random.randint(old_n); d = np.zeros(NB, np.uint8)
            for k in range(NB):
                if np.random.random() < rates[oc, k]: d[k] = 1
            n = classes[np.random.randint(nc)]
            v3 = class_sum(n, d, inc_list, inc_n, outs2, True); feedback(n, d, state, inc_list, inc_n, outs2, v3, False)
@njit(parallel=True)
def scores(Xs, inc_list, inc_n):
    out = np.zeros((len(Xs), 10), np.int32)
    for i in prange(len(Xs)):
        outs = np.zeros(C, np.int8)
        for c in range(10): out[i, c] = class_sum(c, Xs[i], inc_list, inc_n, outs, False)
    return out
state = np.full((10 * C, NL), NST, np.uint8); inc_list = np.zeros((10 * C, LMAX), np.int32); inc_n = np.zeros(10 * C, np.int32); t0 = time.time()
def report(tag, classes):
    sc = scores(Xt, inc_list, inc_n).astype(np.float32); m = np.full(10, -1e9, np.float32); m[classes] = 0; p = (sc + m).argmax(1)
    acc = lambda cl: (p[np.isin(yte, cl)] == yte[np.isin(yte, cl)]).mean(); pr = np.isin(yte, classes)
    print("[%4.0fs] %-34s over %d classes: acc %.4f | old classes %.4f | new classes %s | Shirt recall %.3f" % (time.time() - t0, tag, len(classes), (p[pr] == yte[pr]).mean(), acc(OLD), "%.4f" % acc(NEW) if len(classes) > 6 else "-", (p[yte == 6] == 6).mean() if 6 in classes else float("nan")), flush=True)
def run(classes, rates, dream_p, tag):
    idx = np.where(np.isin(y, classes))[0]
    for e in range(EP):
        order = np.random.RandomState(100 + e + SEED).permutation(idx); train(X, y, order, np.array(classes), rates, dream_p, state, inc_list, inc_n, 1000 + e + SEED); report("%s epoch %d" % (tag, e + 1), classes)
if MODE == "joint": run(OLD + NEW, np.zeros((1, NB)), 0.0, "joint")
else:
    run(OLD, np.zeros((1, NB)), 0.0, "stage 1")
    old_inc = inc_n[:6 * C].copy(); old_state = state[:6 * C].copy()
    rates = np.stack([X[y == c].mean(0) for c in OLD]).astype(np.float64)                          # stored per-class bit frequencies (counters)
    run(NEW, rates, 0.5 if MODE == "dream" else 0.0, "stage 2 (%s)" % MODE)
    print("old banks untouched: %s" % (bool((state[:6 * C] == old_state).all() and (inc_n[:6 * C] == old_inc).all())))
    report("final, all ten classes", OLD + NEW)
