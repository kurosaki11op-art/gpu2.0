"""25 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. tm_genome.py = tm_faithful.py plus connected seeding and growth by surprise (MODE=plain|seed|grow). Base: A FAITHFUL Tsetlin-style clause learner on L's own 4,608-bit code (the earlier tm_sparse.py used positive literals only and stalled at 66%).
Clause = AND of included literals (a bit being on, or a bit being off). Each class has C clauses, half positive-polarity and half negative; class sum = (firing positive) - (firing negative), clipped to +-T. Every literal has a counter (1..2N, included above N).
Learning, per image: target class: each clause is updated with probability (T - sum)/(2T), positive clauses by Type I (reinforce literals that agree with the image when the clause fires, forget with probability 1/s), negative clauses by Type II (when the clause fires wrongly, push excluded literals that are false in this image towards inclusion);
one random other class: each clause with probability (T + sum)/(2T), polarities swapped. No gradients, no multiplies, no matrix, every rule is local to a clause. Inference reads only the included literals of each clause.
env: C (clauses per class, default 100), TT (T), SS (s), BUDGET (seconds of training per call), RESET (1 = start fresh); state kept in the scratchpad between calls."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, CL
from numba import njit, prange
NB = ctr.shape[1]; NL = 2 * NB; C = int(os.environ.get("C", 100)); T = int(os.environ.get("TT", 30)); S = float(os.environ.get("SS", 8.0)); NST = 100; LMAX = int(os.environ.get("LMAX", 64)); BUDGET = float(os.environ.get("BUDGET", 480))
MODE = os.environ.get("MODE", "plain"); EPOCHS = int(os.environ.get("EPOCHS", 3)); CHN, M, F = 4, 6, 32
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
def class_sum(c, x, inc_list, inc_n, train, outs, act):
    v = 0
    for j in range(C):
        if act[c * C + j] == 0:
            outs[j] = 0; continue
        o = fires(c * C + j, x, inc_list, inc_n, train); outs[j] = o
        if o: v += 1 if j % 2 == 0 else -1
    return max(-T, min(T, v))
@njit(parallel=True)
def feedback(c, x, state, inc_list, inc_n, outs, v, positive_target, act):
    p = (T - v) / (2.0 * T) if positive_target else (T + v) / (2.0 * T)
    for j in prange(C):
        if act[c * C + j] == 0: continue
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
        n = 0
        for k in range(NL):
            if state[cl, k] > NST and n < LMAX: inc_list[cl, n] = k; n += 1
        inc_n[cl] = n
@njit
def train_epoch(X, y, order, state, inc_list, inc_n, seed, t_end_check, start, count, act):
    np.random.seed(seed); outs = np.zeros(C, np.int8); outs2 = np.zeros(C, np.int8); done = 0
    for ii in range(start, min(start + count, len(order))):
        i = order[ii]; x = X[i]; c = y[i]
        v = class_sum(c, x, inc_list, inc_n, True, outs, act); feedback(c, x, state, inc_list, inc_n, outs, v, True, act)
        o = (c + 1 + np.random.randint(9)) % 10
        v2 = class_sum(o, x, inc_list, inc_n, True, outs2, act); feedback(o, x, state, inc_list, inc_n, outs2, v2, False, act); done += 1
    return done
@njit
def predict(X, inc_list, inc_n, act):
    out = np.zeros((len(X), 10), np.int32); outs = np.zeros(C, np.int8)
    for i in range(len(X)):
        for c in range(10): out[i, c] = class_sum(c, X[i], inc_list, inc_n, False, outs, act)
    return out

state = np.full((10 * C, NL), NST, np.uint8); inc_list = np.zeros((10 * C, LMAX), np.int32); inc_n = np.zeros(10 * C, np.int32); act = np.zeros(10 * C, np.int8)
t0 = time.time(); X = ctr.astype(np.uint8); y = ytr.astype(np.int64); Xt = cte.astype(np.uint8); rs = np.random.RandomState(1)
def rebuild(cl):
    idx = np.nonzero(state[cl] > NST)[0][:LMAX]; inc_list[cl, :len(idx)] = idx; inc_n[cl] = len(idx)
def candidates(b):
    ch, r = divmod(b, M * M * F); cell, f = divmod(r, F); i, j = divmod(cell, M)
    same = [ch * M * M * F + cell * F + g for g in range(F) if g != f]; spat = [ch * M * M * F + ((i + di) * M + (j + dj)) * F + f for di, dj in ((0, -1), (-1, 0), (-1, -1), (-1, 1)) if 0 <= i + di < M and 0 <= j + dj < M]
    return np.array(same + spat)
CLS_DATA = {c: X[y == c][:3000].astype(np.float32) for c in range(10)}
def parents(b, c, k=3):
    """the k bits that share most counted information with bit b inside class c (learned wiring)"""
    Xc = CLS_DATA[c]; cand = candidates(b); a = Xc[:, b]; pa = a.mean(); P = Xc[:, cand]; pj = P.mean(0); p11 = (a[:, None] * P).mean(0); e = 1e-9; mi = 0
    for pab, pA, pB in ((p11, pa, pj), (pa - p11, pa, 1 - pj), (pj - p11, 1 - pa, pj), (1 - pa - pj + p11, 1 - pa, 1 - pj)): mi = mi + np.maximum(pab, e) * np.log(np.maximum(pab, e) / (max(pA, e) * np.maximum(pB, e)))
    return cand[np.argsort(-mi)[:k]]
def seed_clause(cl, x, c_img):
    """a clause born connected: a seed bit that is on in the image, plus its three information-chosen parents, each taken with the value it has in the image"""
    on = np.nonzero(x)[0]; b = int(on[rs.randint(len(on))]); lits = [b] + [int(p) for p in parents(b, c_img)]
    state[cl, :] = NST
    for l in lits: state[cl, l if x[l] == 1 else NB + l] = NST + 1
    rebuild(cl)
def seed_range(c, js, source):
    for j in js:
        cl = c * C + j; act[cl] = 1
        if source is None: continue
        if j % 2 == 0: i = rs.choice(source["pos"][c])                 # positive clause: an image of this class
        else: i = rs.choice(source["neg"][c])                          # negative clause: an image of another class that this class wrongly claims
        seed_clause(cl, X[i], int(y[i]))
def report(tag):
    sc = predict(Xt, inc_list, inc_n, act).astype(np.float32); p = sc.argmax(1); mk = np.isin(yte, CL); s6 = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("[%4.0fs] %s: test acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | active clauses %d | mean included literals %.1f" % (time.time() - t0, tag, (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap, act.sum(), inc_n[act == 1].mean()), flush=True)
rnd = {"pos": {c: np.where(y == c)[0] for c in range(10)}, "neg": {c: np.where(y != c)[0] for c in range(10)}}
C0 = C // 2 if MODE == "grow" else C
for c in range(10): seed_range(c, range(C0), rnd if MODE in ("seed", "grow") else None)
print("[%4.0fs] MODE=%s: %d clauses per class at start (capacity %d)" % (time.time() - t0, MODE, C0, C), flush=True)
for ep in range(EPOCHS):
    order = np.random.RandomState(100 + ep).permutation(len(X)); pos = 0
    while pos < len(X): pos += train_epoch(X, y, order, state, inc_list, inc_n, 1000 + ep * 7 + pos, 0, pos, 5000, act)
    report("after epoch %d" % (ep + 1))
    if MODE == "grow" and ep == 0:                                                                  # growth by surprise: new clauses seeded where the model under-votes (positive) or over-claims (negative)
        sc = predict(X, inc_list, inc_n, act); src = {"pos": {}, "neg": {}}
        for c in range(10):
            mine = np.where(y == c)[0]; src["pos"][c] = mine[np.argsort(sc[mine, c])[:1500]]; other = np.where(y != c)[0]; src["neg"][c] = other[np.argsort(-sc[other, c])[:1500]]
            seed_range(c, range(C0, C), src)
        print("[%4.0fs] grew to %d clauses per class by surprise" % (time.time() - t0, C), flush=True); report("after growth")
