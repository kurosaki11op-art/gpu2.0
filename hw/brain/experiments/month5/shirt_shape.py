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


GRP = (0, 2, 4, 6)
def train(code, y):
    m = CortexSlow(code.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(len(y)); m.stage(code[sel], y[sel]); return m
main = train(ctr, ytr); Sm = main.S.astype(np.int32)
tot = (centre @ Sm.T); tot = tot * 2 + sum(v @ Sm.T for v in extra); p0 = tot.argmax(1)
gt = np.isin(yte, GRP); gp = np.isin(p0, GRP)
print("main model: overall %.4f, within group (restricted) %.4f" % ((p0 == yte).mean(), (np.array(GRP)[tot[:, GRP].argmax(1)][gt] == yte[gt]).mean()))
def thermo(v, step, n):                      # v: (B, K) integer 0..; -> bits v >= step*k, k = 1..n  (compare only)
    return np.concatenate([(v >= step * k) for k in range(1, n + 1)], 1)
def shape_bits(x, kind):
    im = x.reshape(-1, 28, 28).astype(np.int32); m = im > 40
    cols = np.arange(28)[None, None, :]
    rw = m.sum(2)                                                             # width of the silhouette per row
    lft = np.where(m.any(2), (np.where(m, cols, 99)).min(2), 0); rgt = np.where(m.any(2), (np.where(m, cols, -1)).max(2), 0)
    ch = m.sum(1)                                                             # height per column
    out = []
    if "profile" in kind: out += [thermo(rw, 4, 7), thermo(lft, 4, 7), thermo(27 - rgt, 4, 7), thermo(ch, 4, 7)]
    if "inside" in kind:                                                      # dark pixels between the silhouette edges (placket, collar, buttons)
        inside = (cols >= lft[:, :, None]) & (cols <= rgt[:, :, None]) & (im < 90) & m.any(2)[:, :, None]
        out += [thermo(inside.sum(2), 2, 6)]
    if "top" in kind: out += [(im[:, :10, :] > t).reshape(len(im), -1) for t in (60, 140)]   # neck and shoulder rows at full resolution
    if "edges" in kind:
        gx = np.abs(im[:, :, 1:] - im[:, :, :-1]) > 40; gy = np.abs(im[:, 1:, :] - im[:, :-1, :]) > 40
        out += [gx[:, ::2, ::2].reshape(len(im), -1), gy[:, ::2, ::2].reshape(len(im), -1)]
    return np.concatenate(out, 1).astype(np.int32)
gtr = np.isin(ytr, GRP)
def run(kind):
    ctrg = np.concatenate([ctr[gtr], shape_bits(xtr[gtr], kind)], 1) if kind != "control" else ctr[gtr]
    te_ = np.concatenate([centre, shape_bits(xte, kind)], 1) if kind != "control" else centre
    m = train(ctrg, ytr[gtr]); W = m.S.T.astype(np.int32); sc = te_ @ W
    P = np.array(GRP)[sc[:, GRP].argmax(1)]
    q = p0.copy(); q[gp] = P[gp]
    sh = ytr[gtr] == 6
    print("%-26s extra bits %5d | within group %.4f | Shirt recall %.3f T-shirt recall %.3f | overall %.4f" % (kind, ctrg.shape[1] - ctr.shape[1], (P[gt] == yte[gt]).mean(), (P[yte == 6] == 6).mean(), (P[yte == 0] == 0).mean(), (q == yte).mean()), flush=True)
for kind in os.environ.get("KINDS", "control,profile,inside,top,edges,profile+inside,profile+inside+top,profile+inside+top+edges").split(","): run(kind)
