"""Direct feedback alignment with binary hidden cells (20 Oct 2026) PROBE, SIMULATED, one-pass / few-pass on the shipped coarse code. Integer, adds and compares only, no backward pass.
Hidden layer: H cells, each sums integer synapses over the active input bits (adds), the K strongest cells fire (winner-take-all, binary). Output table (as the chip): class scores = sum of table entries over the active input bits AND the fired hidden cells; margin update (cmax 15).
Error to the hidden cells through FIXED random +-1 connections B (feedback alignment): when the table updates (right class y, best rival r) each FIRED hidden cell j changes its input synapses by sign(B[j,y] - B[j,r]) on the active input bits (three factors: input active, cell fired, error sign). Arms: base (table on the input only), rand (hidden cells fixed at random: control), dfa (hidden cells learn).
usage: DATA_DIR; env DS, H, K, EPOCHS."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from numba import njit
import detector_learn
from cortex_core import load
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); H = int(os.environ.get("H", 1024)); K = int(os.environ.get("K", 64)); EP = int(os.environ.get("EPOCHS", 3)); MARGIN = int(os.environ.get("MARGIN", 256)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
ctr, cte = enc(xtr), enc(xte); NB = ctr.shape[1]


def pack(code):
    na = code.sum(1).astype(np.int32); A = np.zeros((len(code), max(1, na.max())), np.int32)
    for i, row in enumerate(code): idx_ = np.nonzero(row)[0]; A[i, :len(idx_)] = idx_
    return A, na


@njit(cache=False)
def hidden(W1, act, na, K):
    h = W1.shape[0]; pre = np.zeros(h, np.int32)
    for i in range(na):
        b = act[i]
        for j in range(h): pre[j] += W1[j, b]
    order = np.argsort(-pre)[:K]; return order


@njit(cache=False)
def score(W2x, W2h, act, na, fired):
    C = W2x.shape[0]; s = np.zeros(C, np.int32)
    for c in range(C):
        t = 0
        for i in range(na): t += W2x[c, act[i]]
        for f in range(len(fired)): t += W2h[c, fired[f]]
        s[c] = t
    return s


@njit(cache=False)
def train(W1, W2x, W2h, B, A, NA, Y, order_idx, K, margin, cmax, learn_h, use_h):
    for ii in range(len(order_idx)):
        i = order_idx[ii]; act = A[i]; na = NA[i]; y = Y[i]
        fired = hidden(W1, act, na, K) if use_h else np.zeros(0, np.int64)
        s = score(W2x, W2h, act, na, fired); rv = -1; best = -(1 << 30)
        for c in range(len(s)):
            if c != y and s[c] > best: best = s[c]; rv = c
        if s[y] - best > margin: continue
        for t in range(na):
            b = act[t]
            if W2x[y, b] < cmax: W2x[y, b] += 1
            if W2x[rv, b] > -cmax: W2x[rv, b] -= 1
        for f in range(len(fired)):
            j = fired[f]
            if W2h[y, j] < cmax: W2h[y, j] += 1
            if W2h[rv, j] > -cmax: W2h[rv, j] -= 1
            if learn_h:
                d = B[j, y] - B[j, rv]; st = 1 if d > 0 else (-1 if d < 0 else 0)
                if st != 0:
                    for t in range(na):
                        v = W1[j, act[t]] + st
                        W1[j, act[t]] = max(-cmax, min(cmax, v))


@njit(cache=False)
def predict(W1, W2x, W2h, A, NA, K, use_h):
    out = np.zeros(len(A), np.int64)
    for i in range(len(A)):
        fired = hidden(W1, A[i], NA[i], K) if use_h else np.zeros(0, np.int64)
        s = score(W2x, W2h, A[i], NA[i], fired); out[i] = np.argmax(s)
    return out


Atr, NAtr = pack(ctr); Ate, NAte = pack(cte)
for arm in ("base", "rand", "dfa"):
    accs = []
    for seed in (1, 2, 3):
        r = np.random.RandomState(seed); W1 = (r.randint(-1, 2, (H, NB)) * (r.rand(H, NB) < 0.125)).astype(np.int16); W2x = np.zeros((10, NB), np.int16); W2h = np.zeros((10, H), np.int16); B = r.choice([-1, 1], (H, 10)).astype(np.int16)
        for ep in range(EP):
            for st_name, groups in (("once", [tuple(range(10))]),):
                for g in groups:
                    o = np.where(np.isin(ytr, g))[0]; o = o[np.random.RandomState(100 * seed + ep).permutation(len(o))]
                    train(W1, W2x, W2h, B, Atr, NAtr, ytr, o, K, MARGIN, 15, arm == "dfa", arm != "base")
            if ep == 0: first = float((predict(W1, W2x, W2h, Ate, NAte, K, arm != "base") == yte).mean())
        accs.append((first, float((predict(W1, W2x, W2h, Ate, NAte, K, arm != "base") == yte).mean())))
    a = np.mean(accs, 0); print(DS, arm, "H=%d K=%d" % (H, K), "1 epoch %.4f  %d epochs %.4f" % (a[0], EP, a[1]), "%.0fs" % (time.time() - t0), flush=True)
