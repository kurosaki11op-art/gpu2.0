"""(env SLOW=1: CortexSlow, slow table, 18 Oct 2026; env STRIDE1=1: images with detectors at stride 1 and pool 4, 19 Oct 2026.) Final numbers with every adopted option together (16 Oct 2026): margin 32 (default now), word alignment lead 6 for
sound, LOOK AGAIN at test time (images: the picture + 4 one-pixel shifts with the centre counted twice; sound: the word
aligned at start frames 5, 6, 6, 7), IMPRINT + short sleep irrelevant here (no few-shot). Exact integer chip model, 5
seeds, all at once and 5 stages, plus the single-view (no LOOK AGAIN) numbers. usage: DATA_DIR DS"""
import json, os, sys
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
from cortex_slow import CortexSlow
SLOW = True
S1 = True      # images: detectors at stride 1, pool 4 (same 4,608-bit code, finer winner grid)
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    import cochlea_int
    from feature_layer import Features
    f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]
    ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
    v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
    lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
    P0 = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8)
    xtr = cochlea_int.align_word(P0[~te], 6)
    CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
    fes = [Features(64, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)])
    ctr = enc(xtr); views = {L: enc(cochlea_int.align_word(P0[te], L)).astype(np.int32) for L in (5, 6, 7)}
    centre, extra = views[6], [views[5], views[6], views[7]]          # views 5, 6, 6, 7 = centre + [5, 6, 7]
else:
    from feature_layer import Features
    xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    
    CH = (50, 150, ("on", 8), ("off", 8))
    if S1:
        import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
    fes = [Features(32, thr=c, pool=4 if S1 else 2).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)])
    X = xte.reshape(len(xte), 28, 28)

    def shifted(dy, dx):
        out = np.zeros_like(X); ys, yd = (slice(0, 28 - dy), slice(dy, 28)) if dy >= 0 else (slice(-dy, 28), slice(0, 28 + dy))
        xs, xd = (slice(0, 28 - dx), slice(dx, 28)) if dx >= 0 else (slice(-dx, 28), slice(0, 28 + dx))
        out[:, yd, xd] = X[:, ys, xs]; return enc(out.reshape(len(X), -1)).astype(np.int32)

    if S1:
        ctr = enc(xtr)
    centre = enc(xte).astype(np.int32); extra = [shifted(-1, 0), shifted(1, 0), shifted(0, -1), shifted(0, 1)]


import time
from numba import njit
"""Sparse clause learner (Tsetlin-style feedback, positive literals only) on L's own 4,608-bit code. 24 Oct 2026, SIMULATED, one seed.
A clause = a set of included bits; it fires when ALL included bits are active. A class score = (number of firing positive clauses) - (firing negative clauses), clipped to +-T.
Learning = counters (states 1..2N, include when above N) updated with random feedback (Type I reinforces included active bits and forgets inactive ones with probability 1/s,
Type II pushes excluded inactive bits towards inclusion so a falsely firing clause stops firing). No gradients, no multiplies. Inference touches only the active bits (event-driven)."""
NB = ctr.shape[1]; C = int(os.environ.get("CL", 100)); T = int(os.environ.get("TT", 30)); S = float(os.environ.get("SS", 8.0)); NST = 100; EP = int(os.environ.get("EPOCHS", 20))
def csr(code):
    ptr = np.zeros(len(code) + 1, np.int64); idx = []; 
    for i in range(len(code)): w = np.nonzero(code[i])[0].astype(np.int32); idx.append(w); ptr[i + 1] = ptr[i] + len(w)
    return ptr, np.concatenate(idx)
ptr_tr, idx_tr = csr(ctr); ptr_te, idx_te = csr(centre)
@njit(cache=True)
def clause_out(state, ninc, cl_idx, act, train):
    cnt = 0
    for a in act:
        if state[cl_idx, a] > NST: cnt += 1
    if ninc[cl_idx] == 0: return 1 if train else 0
    return 1 if cnt == ninc[cl_idx] else 0
@njit(cache=True)
def class_sum(state, ninc, c, act, train, outs):
    v = 0
    for j in range(C):
        o = clause_out(state, ninc, c * C + j, act, train); outs[j] = o
        if o: v += 1 if j % 2 == 0 else -1
    return max(-T, min(T, v))
@njit(cache=True)
def feedback(state, ninc, c, act, outs, v, positive, mark, rs):
    p = (T - v) / (2.0 * T) if positive else (T + v) / (2.0 * T)
    for j in range(C):
        if np.random.random() > p: continue
        cl = c * C + j; pol_pos = (j % 2 == 0)
        type1 = (pol_pos == positive)
        for a in act: mark[a] = 1
        if type1:
            if outs[j] == 1:
                for a in act:                                    # reinforce included active bits; push others of the active set toward include
                    if np.random.random() < (S - 1.0) / S and state[cl, a] < 2 * NST:
                        state[cl, a] += 1
                        if state[cl, a] == NST + 1: ninc[cl] += 1
                for a in range(state.shape[1]):                  # forget: inactive bits drift to exclude with probability 1/S
                    if mark[a] == 0 and state[cl, a] > 1 and np.random.random() < 1.0 / S:
                        state[cl, a] -= 1
                        if state[cl, a] == NST: ninc[cl] -= 1
            else:
                for a in range(state.shape[1]):
                    if state[cl, a] > 1 and np.random.random() < 1.0 / S:
                        state[cl, a] -= 1
                        if state[cl, a] == NST: ninc[cl] -= 1
        else:
            if outs[j] == 1:                                     # Type II: a falsely firing clause: raise excluded inactive bits
                for a in range(state.shape[1]):
                    if mark[a] == 0 and state[cl, a] <= NST:
                        state[cl, a] += 1
                        if state[cl, a] == NST + 1: ninc[cl] += 1
        for a in act: mark[a] = 0
@njit(cache=True)
def train_epoch(state, ninc, ptr, idx, y, order, seed):
    np.random.seed(seed); outs = np.zeros(C, np.int8); mark = np.zeros(state.shape[1], np.int8)
    for i in order:
        act = idx[ptr[i]:ptr[i + 1]]; c = y[i]
        v = class_sum(state, ninc, c, act, True, outs); feedback(state, ninc, c, act, outs, v, True, mark, 0)
        q = (c + 1 + np.random.randint(0, 9)) % 10
        v = class_sum(state, ninc, q, act, True, outs); feedback(state, ninc, q, act, outs, v, False, mark, 0)
@njit(cache=True)
def predict(state, ninc, ptr, idx):
    n = len(ptr) - 1; out = np.zeros(n, np.int64); outs = np.zeros(C, np.int8)
    for i in range(n):
        act = idx[ptr[i]:ptr[i + 1]]; best = -10 ** 9
        for c in range(10):
            v = class_sum(state, ninc, c, act, False, outs)
            if v > best: best = v; out[i] = c
    return out
state = np.full((10 * C, NB), NST, np.int16); ninc = np.zeros(10 * C, np.int32); y32 = ytr.astype(np.int64); t0 = time.time()
print("clauses per class %d, T %d, s %.1f, code bits %d" % (C, T, S, NB), flush=True)
for ep in range(EP):
    train_epoch(state, ninc, ptr_tr, idx_tr, y32, np.random.RandomState(ep).permutation(len(y32)), ep + 1)
    if ep % 2 == 1 or ep == EP - 1:
        p = predict(state, ninc, ptr_te, idx_te); print("epoch %2d | test accuracy %.4f | Shirt %.3f T-shirt %.3f Pullover %.3f Coat %.3f | included bits per clause %.1f | %.0fs" % (ep + 1, (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[yte == 0] == 0).mean(), (p[yte == 2] == 2).mean(), (p[yte == 4] == 4).mean(), ninc.mean(), time.time() - t0), flush=True)
