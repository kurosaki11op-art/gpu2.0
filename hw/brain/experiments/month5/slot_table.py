"""25 Oct 2026, SIMULATED, one seed. Option B: a counting table that is SPARSE BY CONSTRUCTION. Every code bit keeps at most M slots, each slot = (class, signed integer weight); a class with no slot in a row contributes 0 to that row. Score of a class = sum over the active bits of its slot weight (adds only). Learning is an integer margin rule like L's: for an image of class y, if the true class does not beat the best other class by MARGIN, then in every active bit's row the true class's weight is raised by 1 (it takes a free slot, or the weakest slot if that one is weak, otherwise the weakest slot is worn down by 1 toward zero) and the best wrong class's weight, if it holds a slot there, is lowered by 1.
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
def scores(idx, a, b, cls, w, M, out):
    out[:] = 0
    for t in range(a, b):
        r = idx[t]
        for s in range(M):
            c = cls[r, s]
            if c >= 0: out[c] += w[r, s]
@njit
def train(idx, ptr, y, order, cls, w, M, K, margin, cmax):
    out = np.zeros(K, np.int32); upd = 0
    for ii in range(len(order)):
        i = order[ii]; a = ptr[i]; b = ptr[i + 1]; scores(idx, a, b, cls, w, M, out); yy = y[i]
        best = -1; bv = -1 << 30
        for c in range(K):
            if c != yy and out[c] > bv: bv = out[c]; best = c
        if out[yy] - bv >= margin: continue
        upd += 1
        for t in range(a, b):
            r = idx[t]; sy = -1; sb = -1; free = -1; weak = -1; wv = 1 << 30
            for s in range(M):
                c = cls[r, s]
                if c == yy: sy = s
                elif c == best: sb = s
                if c < 0 and free < 0: free = s
                if c >= 0 and abs(w[r, s]) < wv and c != yy and c != best: wv = abs(w[r, s]); weak = s
            if sy < 0:
                if free >= 0: sy = free; cls[r, sy] = yy; w[r, sy] = 0
                elif weak >= 0:
                    if wv <= 1: sy = weak; cls[r, sy] = yy; w[r, sy] = 0
                    else: w[r, weak] += -1 if w[r, weak] > 0 else 1                           # wear the weakest slot down toward zero
            if sy >= 0 and w[r, sy] < cmax: w[r, sy] += 1
            if sb >= 0 and w[r, sb] > -cmax: w[r, sb] -= 1
    return upd
@njit
def predict(idx, ptr, n, cls, w, M, K):
    out = np.zeros(K, np.int32); p = np.zeros(n, np.int64)
    for i in range(n):
        scores(idx, ptr[i], ptr[i + 1], cls, w, M, out); p[i] = np.argmax(out)
    return p
print("%s: K=%d classes, %d train, %d test images, %d code bits, %.0f active bits per image" % (DATA, K, len(ytr), len(yte), NB, ctr[:2000].sum(1).mean()), flush=True)
act = ctr[:2000].sum(1).mean(); ib = int(np.ceil(np.log2(K))); t0 = time.time()
print("%-6s %-8s %-8s | %-10s %-11s | %-13s %-13s %-9s" % ("slots", "acc", "updates", "table KB", "bits read", "full-table KB", "full bits read", "ratio read"))
for M in MS:
    M = min(M, K); cls = np.full((NB, M), -1, np.int16); w = np.zeros((NB, M), np.int16); rs = np.random.RandomState(1)
    for ep in range(EPOCHS): upd = train(idx_tr, ptr_tr, ytr, rs.permutation(len(ytr)), cls, w, M, K, MARGIN, CMAX)
    p = predict(idx_te, ptr_te, len(yte), cls, w, M, K); acc = (p == yte).mean(); wb = 6                                       # 6-bit signed weight (range +-31)
    used = (cls >= 0).sum(); tab_kb = used * (ib + wb) / 8 / 1024; reads = act * M * (ib + wb); fullkb = NB * K * wb / 8 / 1024; fullr = act * K * wb
    print("%-6d %-8.4f %-8d | %-10.1f %-11.0f | %-13.1f %-13.0f %-9.2f   [%3.0fs]" % (M, acc, upd, tab_kb, reads, fullkb, fullr, fullr / reads, time.time() - t0), flush=True)
