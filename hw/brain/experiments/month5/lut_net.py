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

import torch, torch.nn as nn
torch.set_num_threads(4); torch.manual_seed(0)
h2tr, h2te = hog_bits(xtr, 2), hog_bits(xte, 2)
Atr = torch.tensor(np.concatenate([ctr, h2tr], 1).astype(np.uint8)); Ate = torch.tensor(np.concatenate([centre, h2te], 1).astype(np.uint8)); nb = Atr.shape[1]
Ytr = torch.tensor(ytr); 
def lut_net(per_class, n, epochs, lr=0.05, scale=None, seed=0, tag=""):
    """One layer of trainable lookup tables (weightless): L = 10*per_class LUTs, each reads n fixed random input bits (a table index) and returns one bit
    (table entry > 0). Class score = number of 1-bits in the class's group. Trained on the GPU/CPU with gradients through a sigmoid relaxation of the table entries;
    deployed as tables: inference = n-bit index, 1 lookup per LUT, a popcount per class. No multiply, no matrix."""
    g = torch.Generator().manual_seed(seed); L = 10 * per_class
    conn = torch.randint(0, nb, (L, n), generator=g); pw = (2 ** torch.arange(n)).long()
    W = nn.Parameter(torch.randn(L, 2 ** n, generator=g) * 0.1); opt = torch.optim.Adam([W], lr)
    sc = scale or (4.0 / np.sqrt(per_class))
    def scores(A, hard):
        idx = (A[:, conn].long() * pw).sum(-1)                                       # (B, L) table index
        v = W.t().contiguous()[idx, torch.arange(L)] if False else W[torch.arange(L)[None, :].expand(len(A), -1), idx]
        o = (v > 0).float() if hard else torch.sigmoid(v)
        return o.view(len(A), 10, per_class).sum(2)
    t0 = time.time()
    for ep in range(epochs):
        perm = torch.randperm(len(Atr))
        for i in range(0, len(Atr), 128):
            b = perm[i:i + 128]; loss = nn.functional.cross_entropy(sc * (scores(Atr[b], False) - per_class / 2), Ytr[b]); opt.zero_grad(); loss.backward(); opt.step()
        if ep == epochs - 1 or ep % 3 == 2:
            with torch.no_grad(): p = torch.cat([scores(Ate[j:j + 1000], True).argmax(1) for j in range(0, len(Ate), 1000)]).numpy()
            print("%s epoch %d: hard-table accuracy %.4f | Shirt recall %.3f T-shirt %.3f | tables %.1f KB (1 bit per entry) | %.0fs" % (tag, ep + 1, (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[yte == 0] == 0).mean(), L * 2 ** n / 8 / 1024, time.time() - t0), flush=True)
for pc, n, ep in ((200, 6, 9), (1000, 6, 9), (1000, 8, 9)):
    lut_net(pc, n, ep, tag="LUT layer %d per class, n=%d" % (pc, n))
