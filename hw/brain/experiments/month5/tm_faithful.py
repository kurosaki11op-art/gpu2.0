"""25 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. A FAITHFUL Tsetlin-style clause learner on L's own 4,608-bit code (the earlier tm_sparse.py used positive literals only and stalled at 66%).
Clause = AND of included literals (a bit being on, or a bit being off). Each class has C clauses, half positive-polarity and half negative; class sum = (firing positive) - (firing negative), clipped to +-T. Every literal has a counter (1..2N, included above N).
Learning, per image: target class: each clause is updated with probability (T - sum)/(2T), positive clauses by Type I (reinforce literals that agree with the image when the clause fires, forget with probability 1/s), negative clauses by Type II (when the clause fires wrongly, push excluded literals that are false in this image towards inclusion);
one random other class: each clause with probability (T + sum)/(2T), polarities swapped. No gradients, no multiplies, no matrix, every rule is local to a clause. Inference reads only the included literals of each clause.
env: C (clauses per class, default 100), TT (T), SS (s), BUDGET (seconds of training per call), RESET (1 = start fresh); state kept in the scratchpad between calls."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, CL
from numba import njit, prange
INPUT = os.environ.get('INPUT', 'code')
if INPUT == 'both':                                                                                  # clauses read L's detector bits AND the raw two-threshold pixel bits (4,608 + 1,568 bits)
    from shirt_new_methods_setup import xtr, xte
    def _bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
    ctr, cte = np.concatenate([ctr, _bits(xtr)], 1), np.concatenate([cte, _bits(xte)], 1)
if INPUT == 'raw':                                                                                   # clauses read the raw two-threshold pixel bits (1,568 bits) with no detector front end
    from shirt_new_methods_setup import xtr, xte
    def _bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
    ctr, cte = _bits(xtr), _bits(xte)
if INPUT == 'deep':                                                                                  # piece 4, real depth: layer 2 clauses read L's code + raw pixel bits + the 8,000 firing bits of a frozen layer-1 clause bank (STATE1)
    from shirt_new_methods_setup import xtr, xte
    def _bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
    _b1, _b2 = np.concatenate([ctr, _bits(xtr)], 1).astype(np.uint8), np.concatenate([cte, _bits(xte)], 1).astype(np.uint8)
    _z = np.load(os.environ.get("STATE1", "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/tm_faithful_state_both.npz")); _il, _in = _z["inc_list"], _z["inc_n"]
    @njit(parallel=True)
    def _fire_all(X, il, inn, nb):
        out = np.zeros((len(X), len(inn)), np.uint8)
        for i in prange(len(X)):
            for cl in range(len(inn)):
                n = inn[cl]; ok = 1 if n > 0 else 0
                for t in range(n):
                    lit = il[cl, t]
                    if lit < nb:
                        if X[i, lit] == 0: ok = 0; break
                    elif X[i, lit - nb] == 1: ok = 0; break
                out[i, cl] = ok
        return out
    _f = lambda B: np.concatenate([_fire_all(B[i:i + 5000], _il, _in, B.shape[1]) for i in range(0, len(B), 5000)])
    ctr, cte = np.concatenate([_b1, _f(_b1)], 1), np.concatenate([_b2, _f(_b2)], 1); del _b1, _b2
NB = ctr.shape[1]; NL = 2 * NB; C = int(os.environ.get("C", 100)); T = int(os.environ.get("TT", 30)); S = float(os.environ.get("SS", 8.0)); POS = int(os.environ.get('POSLIT', 0)); SEEDADD = int(os.environ.get('SEEDADD', 0)); NST = 100; LMAX = int(os.environ.get("LMAX", 64)); BUDGET = float(os.environ.get("BUDGET", 480))
CK = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/tm_faithful_state%s.npz" % (("_" + os.environ["INPUT"] if os.environ.get("INPUT", "code") != "code" else "") + ("_pos" if os.environ.get("POSLIT", "0") == "1" else "") + ("_s%s" % os.environ["SEEDADD"] if os.environ.get("SEEDADD") else ""))
@njit
def fires(cl, x, inc_list, inc_n, train):
    n = inc_n[cl]
    if n == 0: return 1 if train else 0
    for t in range(n):
        lit = inc_list[cl, t]
        if lit < NB:
            if x[lit] == 0: return 0
        else:
            if x[lit - NB] == 1: return 0
    return 1
@njit
def class_sum(c, x, inc_list, inc_n, train, outs):
    v = 0
    for j in range(C):
        o = fires(c * C + j, x, inc_list, inc_n, train); outs[j] = o
        if o: v += 1 if j % 2 == 0 else -1
    return max(-T, min(T, v))
@njit(parallel=True)
def feedback(c, x, state, inc_list, inc_n, outs, v, positive_target):
    p = (T - v) / (2.0 * T) if positive_target else (T + v) / (2.0 * T)
    for j in prange(C):
        if np.random.random() > p: continue
        cl = c * C + j; pos_clause = (j % 2 == 0); type1 = (pos_clause == positive_target)
        if type1:
            if outs[j] == 1:
                for k in range(NL):
                    lt = x[k] == 1 if k < NB else x[k - NB] == 0
                    if lt:
                        if np.random.random() < (S - 1.0) / S and state[cl, k] < 2 * NST: state[cl, k] += 1
                    else:
                        if np.random.random() < 1.0 / S and state[cl, k] > 1: state[cl, k] -= 1
            else:
                for k in range(NL):
                    if np.random.random() < 1.0 / S and state[cl, k] > 1: state[cl, k] -= 1
        else:
            if outs[j] == 1:
                for k in range(NL):
                    lt = x[k] == 1 if k < NB else x[k - NB] == 0
                    if (not lt) and state[cl, k] <= NST: state[cl, k] += 1
        if POS == 1:                                                                                         # every clause must hold at least one positive literal, so it can be filed under an active bit
            has = False; bestk = 0; bests = 0
            for k in range(NB):
                if state[cl, k] > NST: has = True; break
                if state[cl, k] > bests: bests = state[cl, k]; bestk = k
            if not has: state[cl, bestk] = NST + 1
        n = 0
        for k in range(NL):
            if state[cl, k] > NST and n < LMAX: inc_list[cl, n] = k; n += 1
        inc_n[cl] = n
@njit
def train_epoch(X, y, order, state, inc_list, inc_n, seed, t_end_check, start, count):
    np.random.seed(seed); outs = np.zeros(C, np.int8); outs2 = np.zeros(C, np.int8); done = 0
    for ii in range(start, min(start + count, len(order))):
        i = order[ii]; x = X[i]; c = y[i]
        v = class_sum(c, x, inc_list, inc_n, True, outs); feedback(c, x, state, inc_list, inc_n, outs, v, True)
        o = (c + 1 + np.random.randint(9)) % 10
        v2 = class_sum(o, x, inc_list, inc_n, True, outs2); feedback(o, x, state, inc_list, inc_n, outs2, v2, False); done += 1
    return done
@njit
def predict(X, inc_list, inc_n):
    out = np.zeros((len(X), 10), np.int32); outs = np.zeros(C, np.int8)
    for i in range(len(X)):
        for c in range(10): out[i, c] = class_sum(c, X[i], inc_list, inc_n, False, outs)
    return out
if os.environ.get("RESET", "0") == "0" and os.path.exists(CK):
    z = np.load(CK); state, inc_list, inc_n, ep, pos = z["state"], z["inc_list"], z["inc_n"], int(z["ep"]), int(z["pos"])
else:
    state = np.full((10 * C, NL), NST, np.uint8); inc_list = np.zeros((10 * C, LMAX), np.int32); inc_n = np.zeros(10 * C, np.int32); ep = 0; pos = 0
t0 = time.time(); X = ctr.astype(np.uint8); y = ytr.astype(np.int64); Xt = cte.astype(np.uint8)
rs = np.random.RandomState(1)
def report(tag):
    sc = predict(Xt, inc_list, inc_n).astype(np.float32); p = sc.argmax(1); mk = np.isin(yte, CL); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("[%4.0fs] %s: test acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | mean included literals per clause %.1f" % (time.time() - t0, tag, (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap, inc_n.mean()), flush=True)
while time.time() - t0 < BUDGET:
    order = np.random.RandomState(100 + ep + SEEDADD).permutation(len(X)); n = train_epoch(X, y, order, state, inc_list, inc_n, 1000 + ep * 7 + pos + SEEDADD, 0, pos, 3000); pos += n
    if pos >= len(X): pos = 0; ep += 1; report("after epoch %d" % ep)
    elif pos % 15000 == 0: report("  epoch %d, %d images" % (ep, pos))
np.savez(CK, state=state, inc_list=inc_list, inc_n=inc_n, ep=ep, pos=pos); report("saved (epoch %d, position %d)" % (ep, pos))
