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
def pairs_select(NC, n_keep, order=2, sub=20000, chunk=20000):
    """Choose conjunction features by COUNTING only: sample NC random AND-features, score each by how much more often it fires inside one class than outside
    (max over classes of P(f|c) - P(f|not c)), keep the best n_keep. Counts, compares, no gradients. Chunked to bound memory."""
    idx = rs.randint(0, nb, (NC, order)); s_ = rs.choice(len(Atr), sub, replace=False); A = Atr[s_]; y = ytr[s_]; best = np.zeros(NC)
    for c0 in range(0, NC, chunk):
        f = np.ones((sub, min(chunk, NC - c0)), np.uint8)
        for j in range(order): f &= A[:, idx[c0:c0 + chunk, j]]
        sc = np.zeros(f.shape[1])
        for c in range(10): sc = np.maximum(sc, f[y == c].mean(0) - f[y != c].mean(0))
        best[c0:c0 + chunk] = sc
    keep = np.argsort(-best)[:n_keep]; return idx[keep]
def expand(A, idx, order=2):
    out = np.ones((len(A), len(idx)), np.uint8)
    for j in range(order): out &= A[:, idx[:, j]]
    return np.concatenate([A, out], 1)
def rep(tag, S, c, t0):
    p = (c @ S.T).argmax(1); print("%-52s bits %6d | accuracy %.4f | Shirt recall %.3f | T-shirt %.3f | %.0fs" % (tag, S.shape[1], (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[yte == 0] == 0).mean(), time.time() - t0), flush=True)
def train(code, y):
    m = CortexSlow(code.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(len(y)); m.stage(code[sel], y[sel]); return m

GRP = (0, 2, 4, 6)
# main model: L slow table, look-again (5 views), as in the shipped scoring
main = train(ctr, ytr); Sm = main.S.astype(np.int32)
tot = 2 * (centre @ Sm.T) + sum(v @ Sm.T for v in extra); p0 = tot.argmax(1)
top2 = np.sort(tot, 1)[:, -2:]; margin = (top2[:, 1] - top2[:, 0]).astype(np.float64)
print("main (look-again): accuracy %.4f | Shirt recall %.3f" % ((p0 == yte).mean(), (p0[yte == 6] == 6).mean()), flush=True)
# stage 2: trained on the four classes only, code = detector code + HOG-style bits + 10,000 count-selected pairwise ANDs
gtr = np.isin(ytr, GRP); idx = pairs_select(100000, 10000, 2)
E2tr, E2te = expand(Atr, idx, 2), expand(Ate, idx, 2)
m2 = CortexSlow(E2tr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(int(gtr.sum())); m2.stage(E2tr[gtr][sel], ytr[gtr][sel])
S2 = m2.S.astype(np.int32)
sc2 = np.concatenate([(E2te[i:i + 2000].astype(np.int32) @ S2.T) for i in range(0, len(E2te), 2000)])
p2 = np.array(GRP)[sc2[:, GRP].argmax(1)]
act_main = float(centre.sum(1).mean()); act2 = float(E2te.sum(1).mean())
print("stage-2 table: 4 classes x %d bits = %.0f KB at 8 bit, %.0f KB at 2 bit | active rows per image: main %.0f (centre view), stage 2 %.0f" % (E2tr.shape[1], 4 * E2tr.shape[1] / 1024, 4 * E2tr.shape[1] / 4 / 1024, act_main, act2), flush=True)
ing = np.isin(p0, GRP)
print("| gate (margin below percentile of group-predicted images) | images sent to stage 2 | accuracy | Shirt recall | T-shirt recall | extra active rows per image (average) |\n|---|---|---|---|---|---|")
for pct in (0, 10, 25, 50, 75, 100):
    thr = np.percentile(margin[ing], pct) if pct else -1
    gate = ing & (margin <= thr) if pct else np.zeros(len(yte), bool)
    q = p0.copy(); q[gate] = p2[gate]
    print("| %3d %% | %.1f %% | %.4f | %.3f | %.3f | %.0f |" % (pct, 100 * gate.mean(), (q == yte).mean(), (q[yte == 6] == 6).mean(), (q[yte == 0] == 0).mean(), act2 * gate.mean()), flush=True)
