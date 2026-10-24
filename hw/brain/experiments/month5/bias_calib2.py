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


"""Bias calibration by counting (24 Oct 2026, SIMULATED, Fashion-MNIST, single view). Failure studied: the table favours T-shirt over Shirt (T-shirt recall 88%, Shirt 64%).
A per-class offset (one integer add per class) is learned on 10,000 held-out TRAINING images (coordinate search maximising accuracy, then also maximising the mean of Shirt and T-shirt recall) and applied to the test scores. Trained table: first 50,000 images."""
ntr = 50000
m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(ntr); m.stage(ctr[:ntr][sel], ytr[:ntr][sel]); S = m.S.astype(np.int32)
sv = ctr[ntr:].astype(np.int32) @ S.T; st = centre @ S.T; yv = ytr[ntr:]
def rep(tag, sc):
    p = sc.argmax(1); print("%-52s accuracy %.4f | Shirt %.3f T-shirt %.3f Pullover %.3f Coat %.3f" % (tag, (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[yte == 0] == 0).mean(), (p[yte == 2] == 2).mean(), (p[yte == 4] == 4).mean()), flush=True)
rep("no offsets", st)
def fit(objective):
    b = np.zeros(10); scale = float(np.std(sv)) 
    for rnd in range(4):
        for c in range(10):
            best = (objective(sv + b), b[c])
            for d in np.linspace(-0.6, 0.6, 25) * scale:
                bb = b.copy(); bb[c] = d; v = objective(sv + bb)
                if v > best[0]: best = (v, d)
            b[c] = best[1]
    return b
acc_obj = lambda s: (s.argmax(1) == yv).mean()
bal_obj = lambda s: np.mean([(s.argmax(1)[yv == c] == c).mean() for c in range(10)])
sh_obj = lambda s: 0.5 * ((s.argmax(1)[yv == 6] == 6).mean() + (s.argmax(1)[yv == 0] == 0).mean()) + 0.3 * (s.argmax(1) == yv).mean()
for tag, obj in (("offsets maximising accuracy (validation)", acc_obj), ("offsets maximising mean class recall", bal_obj), ("offsets favouring Shirt + T-shirt recall", sh_obj)):
    b = fit(obj); rep(tag, st + b); print("   offsets:", np.round(b / (np.std(sv) + 1e-9), 2))
