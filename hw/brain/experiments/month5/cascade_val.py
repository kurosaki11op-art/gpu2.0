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
def hog_bits(x, cell, nb=8, levels=(1, 3, 6, 10), ste=None):
    im = x.reshape(-1, 28, 28).astype(np.int32)
    p = np.pad(im, ((0, 0), (1, 1), (1, 1)), mode="edge")
    gx = p[:, 1:-1, 2:] - p[:, 1:-1, :-2]; gy = p[:, 2:, 1:-1] - p[:, :-2, 1:-1]          # subtractions only
    ax, ay = np.abs(gx), np.abs(gy); mag = ax + ay
    # orientation in 8 bins of the full circle from signs and magnitude compares (ratios 3/8 and 5/2 are shift-adds in hardware)
    sx, sy = gx >= 0, gy >= 0
    flat = (8 * ay <= 3 * ax); steep = (8 * ax <= 3 * ay)
    diag = ~flat & ~steep
    b = np.where(flat, np.where(sx, 0, 4), np.where(steep, np.where(sy, 2, 6), np.where(sx == sy, np.where(sx, 1, 5), np.where(sx, 7, 3))))
    strong = mag > 24
    n = 28 // cell; out = []
    for k in range(nb):
        m = ((b == k) & strong).reshape(-1, n, cell, n, cell).sum((2, 4))            # count of strong edges of this orientation per cell
        out.append(m.reshape(len(im), -1))
    hist = np.stack(out, 2).reshape(len(im), -1)                                         # (N, cells*nb) integer counts
    lv = levels if cell == 4 else (1, 2, 3)
    return np.concatenate([(hist >= t) for t in lv], 1).astype(np.int32)
def train(code, y):
    m = CortexSlow(code.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(len(y)); m.stage(code[sel], y[sel]); return m
def rep(tag, S, c, t0):
    p = (c @ S.T).argmax(1); print("%-46s bits %5d | accuracy %.4f | Shirt recall %.3f | T-shirt recall %.3f | Pullover %.3f | Coat %.3f | %.0fs" % (tag, S.shape[1], (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[yte == 0] == 0).mean(), (p[yte == 2] == 2).mean(), (p[yte == 4] == 4).mean(), time.time() - t0), flush=True)

import torch
t0 = time.time()
h2tr, h2te = hog_bits(xtr, 2), hog_bits(xte, 2)
Atr, Ate = np.concatenate([ctr, h2tr], 1).astype(np.uint8), np.concatenate([centre, h2te], 1).astype(np.uint8); nb = Atr.shape[1]
rs = np.random.RandomState(0)

GRP = (0, 2, 4, 6); ntr = 50000
def pairs_select(A, y, NC, n_keep, order=2, sub=20000, chunk=20000, seed=0):
    r = np.random.RandomState(seed); idx = r.randint(0, A.shape[1], (NC, order)); s_ = r.choice(len(A), sub, replace=False); A = A[s_]; y = y[s_]; best = np.zeros(NC)
    for c0 in range(0, NC, chunk):
        f = np.ones((sub, min(chunk, NC - c0)), np.uint8)
        for j in range(order): f &= A[:, idx[c0:c0 + chunk, j]]
        sc = np.zeros(f.shape[1])
        for c in range(10): sc = np.maximum(sc, f[y == c].mean(0) - f[y != c].mean(0))
        best[c0:c0 + chunk] = sc
    return idx[np.argsort(-best)[:n_keep]]
def expand(A, idx, order=2):
    out = np.ones((len(A), len(idx)), np.uint8)
    for j in range(order): out &= A[:, idx[:, j]]
    return np.concatenate([A, out], 1)
# held-out validation: the last 10,000 training images are NOT used to train either stage, they choose the gate
y_tr, y_va = ytr[:ntr], ytr[ntr:]
main = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(ntr); main.stage(ctr[:ntr][sel], y_tr[sel]); S1 = main.S.astype(np.int32)
sc_va = ctr[ntr:].astype(np.int32) @ S1.T; sc_te = centre @ S1.T
def top2m(sc): t = np.sort(sc, 1)[:, -2:]; return (t[:, 1] - t[:, 0]).astype(float)
m_va, m_te = top2m(sc_va), top2m(sc_te); p_va, p_te = sc_va.argmax(1), sc_te.argmax(1)
print("stage 1 (single view): validation accuracy %.4f | test accuracy %.4f | test Shirt recall %.3f" % ((p_va == y_va).mean(), (p_te == yte).mean(), (p_te[yte == 6] == 6).mean()), flush=True)
idx = pairs_select(Atr[:ntr], y_tr, 100000, 10000)
E2 = expand(np.concatenate([Atr, Ate], 0), idx); E2tr, E2va, E2te = E2[:ntr], E2[ntr:len(Atr)], E2[len(Atr):]
g = np.isin(y_tr, GRP); m2 = CortexSlow(E2.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(int(g.sum())); m2.stage(E2tr[g][sel], y_tr[g][sel]); S2 = m2.S.astype(np.int32)
G = np.array(GRP); s2 = lambda E: np.concatenate([E[i:i + 2000].astype(np.int32) @ S2.T for i in range(0, len(E), 2000)])
q_va = G[s2(E2va)[:, GRP].argmax(1)]; q_te = G[s2(E2te)[:, GRP].argmax(1)]
ing_va, ing_te = np.isin(p_va, GRP), np.isin(p_te, GRP)
def apply(p, q, ing, m, thr): gt = ing & (m <= thr); o = p.copy(); o[gt] = q[gt]; return o, gt
grid = [-1] + [float(np.percentile(m_va[ing_va], pc)) for pc in range(5, 101, 5)]
best = (-1, None)
print("| threshold (percentile of validation margins) | val gated | val accuracy | test gated | test accuracy | test Shirt recall |\n|---|---|---|---|---|---|")
for k, thr in enumerate(grid):
    ov, gv = apply(p_va, q_va, ing_va, m_va, thr); ot, gt = apply(p_te, q_te, ing_te, m_te, thr)
    print("| %3d %% | %.1f %% | %.4f | %.1f %% | %.4f | %.3f |" % (5 * k, 100 * gv.mean(), (ov == y_va).mean(), 100 * gt.mean(), (ot == yte).mean(), (ot[yte == 6] == 6).mean()), flush=True)
    if (ov == y_va).mean() > best[0]: best = ((ov == y_va).mean(), (5 * k, thr))
pc, thr = best[1]; ot, gt = apply(p_te, q_te, ing_te, m_te, thr)
print("\nthreshold chosen on VALIDATION only: percentile %d, validation accuracy %.4f -> TEST accuracy %.4f (stage 1 alone %.4f), Shirt recall %.3f (stage 1 alone %.3f), T-shirt recall %.3f, %.1f %% of test images sent to stage 2, extra active rows per image %.0f"
      % (pc, best[0], (ot == yte).mean(), (p_te == yte).mean(), (ot[yte == 6] == 6).mean(), (p_te[yte == 6] == 6).mean(), (ot[yte == 0] == 0).mean(), 100 * gt.mean(), E2te.sum(1).mean() * gt.mean()))
