"""(sketch variant of slot_table.py) 25 Oct 2026, SIMULATED, one seed. Option B2: a counter SKETCH. Every code bit keeps a fixed row of R counters; class c uses counter H[bit, c] of that row, where H is a per-bit hash of the class (assumed computed by a few XOR and rotate gates, not stored); several classes share a counter, and different bits hash differently so collisions average out. Score of class c = sum over active bits of the counter H[bit, c] (adds only); the margin update raises the true class's counter and lowers the best wrong class's counter. Row size is R whatever K is, and no class index is stored.
Option B: a counting table that is SPARSE BY CONSTRUCTION. Every code bit keeps at most M slots, each slot = (class, signed integer weight); a class with no slot in a row contributes 0 to that row. Score of a class = sum over the active bits of its slot weight (adds only). Learning is an integer margin rule like L's: for an image of class y, if the true class does not beat the best other class by MARGIN, then in every active bit's row the true class's weight is raised by 1 (it takes a free slot, or the weakest slot if that one is weak, otherwise the weakest slot is worn down by 1 toward zero) and the best wrong class's weight, if it holds a slot there, is lowered by 1.
M = K is the full table (same learner), the fair reference. Data: EMNIST-balanced codes (47 classes, L's detector code, cached by emnist_c1.py) or Fashion-MNIST codes (10 classes).
env: DATA (emnist|fashion), K, EPOCHS, MARGIN, CMAX, MS (comma list of slot counts)"""
import os, sys, time
import numpy as np
from numba import njit
E = lambda k, d: type(d)(os.environ.get(k, d))
DATA, K, EPOCHS, MARGIN, CMAX, MS = E("DATA", "emnist"), E("K", 47), E("EPOCHS", 8), E("MARGIN", 8), E("CMAX", 31), [int(m) for m in E("MS", "2,4,8,16,47").split(",")]
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"
if DATA == "emnist":
    z = np.load(SP + "emnist_codes.npz"); ctr, ytr, cte, yte = z["ctr"], z["ytr"], z["cte"], z["yte"]
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
    from shirt_new_methods_setup import ctr, cte, ytr, yte
tr, te = ytr < K, yte < K; ctr, ytr, cte, yte = ctr[tr], ytr[tr].astype(np.int64), cte[te], yte[te].astype(np.int64); NB = ctr.shape[1]
def csr(code):
    ptr = np.zeros(len(code) + 1, np.int64); idx = []
    for i in range(len(code)): w = np.nonzero(code[i])[0].astype(np.int32); idx.append(w); ptr[i + 1] = ptr[i] + len(w)
    return ptr, np.concatenate(idx)
ptr_tr, idx_tr = csr(ctr); ptr_te, idx_te = csr(cte)

@njit
def scores(idx, a, b, H, w, K, out):
    out[:] = 0
    for t in range(a, b):
        r = idx[t]
        for c in range(K): out[c] += w[r, H[r, c]]
@njit
def train(idx, ptr, y, order, H, w, K, margin, cmax):
    out = np.zeros(K, np.int32); upd = 0
    for ii in range(len(order)):
        i = order[ii]; a = ptr[i]; b = ptr[i + 1]; scores(idx, a, b, H, w, K, out); yy = y[i]
        best = -1; bv = -1 << 30
        for c in range(K):
            if c != yy and out[c] > bv: bv = out[c]; best = c
        if out[yy] - bv >= margin: continue
        upd += 1
        for t in range(a, b):
            r = idx[t]; hy = H[r, yy]; hb = H[r, best]
            if hy != hb:
                if w[r, hy] < cmax: w[r, hy] += 1
                if w[r, hb] > -cmax: w[r, hb] -= 1
    return upd
@njit
def predict(idx, ptr, n, H, w, K):
    out = np.zeros(K, np.int32); p = np.zeros(n, np.int64)
    for i in range(n):
        scores(idx, ptr[i], ptr[i + 1], H, w, K, out); p[i] = np.argmax(out)
    return p
print("%s: K=%d classes, %d train, %d test images, %d code bits, %.0f active bits per image" % (DATA, K, len(ytr), len(yte), NB, ctr[:2000].sum(1).mean()), flush=True)
act = ctr[:2000].sum(1).mean(); t0 = time.time(); wb = 6
print("%-6s %-8s %-8s | %-10s %-11s | %-13s %-13s %-9s" % ("R", "acc", "updates", "table KB", "bits read", "full-table KB", "full bits read", "ratio read"))
for R in MS:
    R = min(R, K); H = np.random.RandomState(7).randint(0, R, (NB, K)).astype(np.int16); w = np.zeros((NB, R), np.int16); rs = np.random.RandomState(1)
    for ep in range(EPOCHS): upd = train(idx_tr, ptr_tr, ytr, rs.permutation(len(ytr)), H, w, K, MARGIN, CMAX)
    p = predict(idx_te, ptr_te, len(yte), H, w, K); acc = (p == yte).mean()
    tab_kb = NB * R * wb / 8 / 1024; reads = act * R * wb; fullkb = NB * K * wb / 8 / 1024; fullr = act * K * wb
    print("%-6d %-8.4f %-8d | %-10.1f %-11.0f | %-13.1f %-13.0f %-9.2f   [%3.0fs]" % (R, acc, upd, tab_kb, reads, fullkb, fullr, fullr / reads, time.time() - t0), flush=True)
