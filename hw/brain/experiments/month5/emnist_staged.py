"""26 Oct 2026, SIMULATED, EMNIST-balanced (47 classes), one seed. Does the continual-learning design hold on a second dataset with many classes? Clause learner (tm_faithful.py rule) with literals = L's detector code + raw 2-threshold pixel bits (6,176 bits), C clauses per class.
MODE=joint: all 47 classes together (reference). MODE=stage: stage 1 trains classes 0-23; stage 2 adds classes 24-46 with unfrozen rehearsal: class-balanced stream, new classes from their full data, old classes only from E stored images each (random), each rehearsal image a recombination of two stored images of the class plus FLIP noise. Offset added to old-class sums swept; the label-free rule picks the offset whose share of test images assigned to old classes is closest to the old classes' share of the stream.
env: MODE, C, TT, EP (joint / stage 1 epochs), STEPS (stage 2), E, FLIP."""
import os, sys, time, gzip
import numpy as np
from numba import njit, prange
E_ = lambda k, d: type(d)(os.environ.get(k, d))
MODE = E_("MODE", "stage"); C = E_("C", 120); T = E_("TT", 12); S = 3.0; NST = 100; LMAX = 256; EP = E_("EP", 3); STEPS = E_("STEPS", 200000); NE = E_("E", 20); FLIP = E_("FLIP", 0.02); K = 47; KO = 24
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"
z = np.load(SP + "emnist_codes.npz"); ctr, y, cte, yte = z["ctr"], z["ytr"].astype(np.int64), z["cte"], z["yte"]
D = "/tmp/emnist_bal"; rd = lambda f, off: np.frombuffer(gzip.open(os.path.join(D, "emnist-balanced-" + f)).read(), np.uint8, offset=off)
xtr, xte = rd("train-images-idx3-ubyte.gz", 16).reshape(-1, 784), rd("test-images-idx3-ubyte.gz", 16).reshape(-1, 784); rs0 = np.random.RandomState(0); itr = rs0.permutation(len(xtr))[:40000]; ite = rs0.permutation(len(xte))[:10000]; xtr, xte = xtr[itr], xte[ite]
def bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
X = np.concatenate([ctr, bits(xtr)], 1).astype(np.uint8); Xt = np.concatenate([cte, bits(xte)], 1).astype(np.uint8); NB = X.shape[1]; NL = 2 * NB
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
def train_plain(Xs, ys, order, classes, state, inc_list, inc_n, seed):
    np.random.seed(seed); outs = np.zeros(C, np.int8); outs2 = np.zeros(C, np.int8); nc = len(classes)
    for ii in range(len(order)):
        i = order[ii]; x = Xs[i]; a = ys[i]
        v = class_sum(a, x, inc_list, inc_n, outs, True); feedback(a, x, state, inc_list, inc_n, outs, v, True)
        o = classes[np.random.randint(nc)]
        while o == a: o = classes[np.random.randint(nc)]
        v2 = class_sum(o, x, inc_list, inc_n, outs2, True); feedback(o, x, state, inc_list, inc_n, outs2, v2, False)
@njit
def stream(Xs, newidx, newlen, EX, state, inc_list, inc_n, steps, seed, flip):
    np.random.seed(seed); outs = np.zeros(C, np.int8); outs2 = np.zeros(C, np.int8)
    for s in range(steps):
        a = np.random.randint(K)
        if a < KO:
            x = EX[a, np.random.randint(EX.shape[1])].copy(); x2 = EX[a, np.random.randint(EX.shape[1])]
            for k in range(len(x)):
                if x[k] != x2[k] and np.random.random() < 0.5: x[k] = x2[k]
                if np.random.random() < flip: x[k] = 1 - x[k]
        else: x = Xs[newidx[a - KO, np.random.randint(newlen[a - KO])]]
        v = class_sum(a, x, inc_list, inc_n, outs, True); feedback(a, x, state, inc_list, inc_n, outs, v, True)
        o = (a + 1 + np.random.randint(K - 1)) % K
        v2 = class_sum(o, x, inc_list, inc_n, outs2, True); feedback(o, x, state, inc_list, inc_n, outs2, v2, False)
@njit(parallel=True)
def scores(Xs, inc_list, inc_n):
    out = np.zeros((len(Xs), K), np.int32)
    for i in prange(len(Xs)):
        outs = np.zeros(C, np.int8)
        for c in range(K): out[i, c] = class_sum(c, Xs[i], inc_list, inc_n, outs, False)
    return out
state = np.full((K * C, NL), NST, np.uint8); inc_list = np.zeros((K * C, LMAX), np.int32); inc_n = np.zeros(K * C, np.int32); t0 = time.time(); om = yte < KO
def rep(tag, classes_mask=None, offs=(0,)):
    so = scores(Xt, inc_list, inc_n).astype(np.float32)
    for off in offs:
        s_ = so.copy(); s_[:, :KO] += off
        if classes_mask is not None: s_[:, ~classes_mask] = -1e9
        p = s_.argmax(1); sel = np.ones(len(yte), bool) if classes_mask is None else classes_mask[yte]
        print("RESULT %s offset %+d: all %.4f | old %.4f | new %s | share predicted old %.3f (stream share %.3f) [%.0fs]" % (tag, off, (p[sel] == yte[sel]).mean(), (p[om] == yte[om]).mean(), "%.4f" % (p[~om] == yte[~om]).mean() if (~om).any() and (classes_mask is None or classes_mask[KO:].any()) else "-", (p[sel] < KO).mean(), KO / K, time.time() - t0), flush=True)
if MODE == "joint":
    for e in range(EP):
        train_plain(X, y, np.random.RandomState(100 + e).permutation(len(X)), np.arange(K), state, inc_list, inc_n, 1000 + e); rep("joint epoch %d" % (e + 1), None, (0, 10, 20))
else:
    ck = SP + "emnist_s1.npz"; cm = np.zeros(K, bool); cm[:KO] = True; idx1 = np.where(y < KO)[0]
    if os.path.exists(ck): zz = np.load(ck); state[:] = zz["state"]; inc_list[:] = zz["inc_list"]; inc_n[:] = zz["inc_n"]; rep("stage 1 (loaded), old classes only", cm)
    else:
        for e in range(EP): train_plain(X, y, np.random.RandomState(100 + e).permutation(idx1), np.arange(KO), state, inc_list, inc_n, 1000 + e); rep("stage 1 epoch %d, old classes only" % (e + 1), cm)
        np.savez(ck, state=state, inc_list=inc_list, inc_n=inc_n)
    rs = np.random.RandomState(3); EX = np.stack([X[rs.choice(np.where(y == c)[0], NE, replace=False)] for c in range(KO)])
    ni = [np.where(y == c)[0] for c in range(KO, K)]; nl = np.array([len(i) for i in ni]); NI = np.zeros((len(ni), nl.max()), np.int64)
    for j, i in enumerate(ni): NI[j, :len(i)] = i
    for r in range(STEPS // 50000):
        stream(X, NI, nl, EX, state, inc_list, inc_n, 50000, 11 + r, FLIP); rep("staged E=%d steps %d" % (NE, 50000 * (r + 1)), None, (0, 2, 4, 6, 8, 10, 14))
