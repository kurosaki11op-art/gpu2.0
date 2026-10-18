"""Max-over-shift matching at test time for new words (from the GPU few-shot literature: banded DTW / vocal-tract-length warps, here as MAX instead of SUM over views).
Chip knows words 0-4, learns 5-9 from k recordings (IMPRINT + short sleep, aligned codes, detectors fitted on words 0-1). Test clip scored on views: word start at frames 4..8
and one frequency row up / down (at start frame 6). Decisions: single (6) | sum over (5,6,6,7) (LOOK AGAIN) | max over (5,6,7) | max over (4..8) | max over time and rows (7 views) |
sum of max-pooled... Per-class score = max (or sum) over views of the integer table score. 3 draws, k = 1, 2, 5. SIMULATED. usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea_int
from feature_layer import Features
from cortex_int import CortexInt
D = sys.argv[1]
f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]
ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
P0 = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8)
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
fes = [Features(64, thr=c).fit(cochlea_int.align_word(P0[~te], 6)[np.isin(ytr, (0, 1))][:12000]) for c in CH]
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 4000]) for g in fes], 1) for i in range(0, len(x), 4000)])


def shiftrows(x, d):
    im = x.reshape(len(x), 28, 28); out = np.zeros_like(im)
    if d > 0: out[:, d:, :] = im[:, :-d, :]
    elif d < 0: out[:, :d, :] = im[:, -d:, :]
    else: out = im
    return out.reshape(len(x), -1)


Ptr, Pte = P0[~te], P0[te]
c6 = enc(cochlea_int.align_word(Ptr, 6))
views = {("t", L): enc(cochlea_int.align_word(Pte, L)).astype(np.int32) for L in (4, 5, 6, 7, 8)}
base6 = cochlea_int.align_word(Pte, 6)
views[("r", 1)] = enc(shiftrows(base6, 1)).astype(np.int32); views[("r", -1)] = enc(shiftrows(base6, -1)).astype(np.int32)
old_te, new_te = yte < 5, yte >= 5
for k in (1, 2, 5):
    rows = {}
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s); so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
        sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
        m = CortexInt(c6.shape[1], seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2); m.stage(c6[so], ytr[so]); m.stage(c6[sn], ytr[sn])
        W = m.W.T.astype(np.int32); sc = {key: val @ W for key, val in views.items()}
        T = [sc[("t", L)] for L in (5, 6, 7)]; T5 = [sc[("t", L)] for L in (4, 5, 6, 7, 8)]; R = [sc[("r", 1)], sc[("r", -1)]]
        dec = {"single": sc[("t", 6)], "sum 5,6,6,7": sc[("t", 5)] + 2 * sc[("t", 6)] + sc[("t", 7)], "max 5,6,7": np.max(T, 0), "max 4..8": np.max(T5, 0),
               "max time+rows": np.max(T5 + R, 0), "sum time+rows": sum(T5 + R)}
        for name, scr in dec.items():
            p = scr.argmax(1); rows.setdefault(name, []).append(((p == yte).mean(), (p[new_te] == yte[new_te]).mean(), (p[old_te] == yte[old_te]).mean()))
    for name, vv in rows.items():
        a = np.mean(vv, 0); print(f"k={k} {name:14s}: all-10 {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}", flush=True)
