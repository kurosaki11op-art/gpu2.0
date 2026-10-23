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
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 400]) for g in fes], 1) for i in range(0, len(x), 400)])
    ctr = enc(xtr); views = {L: enc(cochlea_int.align_word(P0[te], L)).astype(np.int32) for L in (5, 6, 7)}
    centre, extra = views[6], [views[5], views[6], views[7]]          # views 5, 6, 6, 7 = centre + [5, 6, 7]
else:
    from feature_layer import Features
    xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    
    CH = (50, 150, ("on", 8), ("off", 8))
    if S1:
        import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
    fes = [Features(32, thr=c, pool=4 if S1 else 2).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 400]) for g in fes], 1) for i in range(0, len(x), 400)])
    X = xte.reshape(len(xte), 28, 28)

    def shifted(dy, dx):
        out = np.zeros_like(X); ys, yd = (slice(0, 28 - dy), slice(dy, 28)) if dy >= 0 else (slice(-dy, 28), slice(0, 28 + dy))
        xs, xd = (slice(0, 28 - dx), slice(dx, 28)) if dx >= 0 else (slice(-dx, 28), slice(0, 28 + dx))
        out[:, yd, xd] = X[:, ys, xs]; return enc(out.reshape(len(X), -1)).astype(np.int32)

    if S1:
        ctr = enc(xtr)
    centre = enc(xte).astype(np.int32); extra = [shifted(-1, 0), shifted(1, 0), shifted(0, -1), shifted(0, 1)]


import feature_layer
GRP = (0, 2, 4, 6)                       # T-shirt, Pullover, Coat, Shirt
def train(code, y, seed=1):
    m = CortexSlow(code.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=seed); sel = np.random.RandomState(100).permutation(len(y)); m.stage(code[sel], y[sel]); return m
main = train(ctr, ytr); Sm = main.S.astype(np.int32)
tot = (centre @ Sm.T); tot = tot * 2 + sum(v @ Sm.T for v in extra); p0 = tot.argmax(1)
print("main model: overall %.4f" % (p0 == yte).mean())
gt = np.isin(yte, GRP); gp = np.isin(p0, GRP)
def within(P, name):                        # accuracy among test items whose true class is in the group (4-way)
    print("  %-34s 4-way within group %.4f" % (name, (P[gt] == yte[gt]).mean()))
sc = np.array(GRP)
within(np.array(GRP)[tot[:, GRP].argmax(1)], "main model restricted to group")
gtr = np.isin(ytr, GRP); xg = xtr[gtr]
def spec(name, fesg, pool_ps_st):
    feature_layer.PS, feature_layer.ST = pool_ps_st
    e = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 400]) for g in fesg], 1) for i in range(0, len(x), 400)])
    c = e(xtr[gtr]).astype(np.int32); yg = ytr[gtr]
    t = e(xte); views = [t.astype(np.int32)]
    X = xte.reshape(len(xte), 28, 28)
    def sh(dy, dx):
        out = np.zeros_like(X); ys, yd = (slice(0, 28 - dy), slice(dy, 28)) if dy >= 0 else (slice(-dy, 28), slice(0, 28 + dy))
        xs, xd = (slice(0, 28 - dx), slice(dx, 28)) if dx >= 0 else (slice(-dx, 28), slice(0, 28 + dx)); out[:, yd, xd] = X[:, ys, xs]; return e(out.reshape(len(X), -1)).astype(np.int32)
    ex = [sh(-1, 0), sh(1, 0), sh(0, -1), sh(0, 1)]
    m = CortexSlow(c.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1)
    # the model needs class ids 0..n-1 in its own table of 10 rows: keep original ids
    sel = np.random.RandomState(100).permutation(len(yg)); m.stage(c[sel], yg[sel])
    W = m.S.T.astype(np.int32); tt = 2 * (views[0] @ W) + sum(v @ W for v in ex)
    P = np.array(GRP)[tt[:, GRP].argmax(1)]; within(P, name)
    q = p0.copy(); q[gp] = P[gp]; print("     overall if group decided by this specialist: %.4f (main %.4f), code bits %d" % ((q == yte).mean(), (p0 == yte).mean(), c.shape[1]))
CH = (50, 150, ("on", 8), ("off", 8))
if not os.environ.get("FINE"): spec("same code, group-only training", [Features(32, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH], (5, 1))
if not os.environ.get("FINE"): spec("detectors fitted on group, pool 4", [Features(32, thr=c, pool=4).fit(xg[:12000]) for c in CH], (5, 1))
spec("detectors on group, F64 pool 2", [Features(64, thr=c, pool=2).fit(xg[:12000]) for c in CH], (5, 1))
spec("detectors on group, F64 pool 2 PS7", [Features(64, thr=c, pool=2).fit(xg[:12000]) for c in CH], (7, 1))
