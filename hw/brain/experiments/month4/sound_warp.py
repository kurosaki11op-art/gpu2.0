"""Sound, beyond word alignment (lead 6): (a) tempo normalisation - the word (from its start, first frame >= 3/4 of
the loudest, to its end, last frame >= END of the loudest) is stretched or squeezed to L frames starting at frame 6
(nearest frame, the source column advanced by an add-and-compare step counter: no divide); (b) pitch normalisation -
rows (resonators) shifted so the picture's loudness centre row (running sum reaching half the total) lands on a fixed
row, shift capped at +-R. Integer cochlea + floor, 10 x 64 encoder, exact integer chip model, 3 seeds, all at once.
usage: DATA_DIR [variant ...]"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea_int
from feature_layer import Features
from cortex_int import CortexInt
D = sys.argv[1]
z = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = z["S"], z["y"], z["te"]
ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
P0 = np.clip(255 - (top - lg) * 8, 0, 255).astype(np.uint8)                       # (clip, resonator row, frame)


def warp(P0, L, end_num, end_den, lead=6):
    loud = P0.astype(np.int64).sum(1); mx = loud.max(1)
    out = np.zeros_like(P0)
    for i in range(len(P0)):
        st = int(np.argmax(loud[i] >= (mx[i] * 3 >> 2)))
        on = np.nonzero(loud[i] * end_den >= mx[i] * end_num)[0]; en = int(on[-1]) if len(on) else st
        en = max(en, st); d = en - st + 1
        acc, src = 0, st                                                            # Bresenham step: src += d/L per column
        for j in range(L):
            c = lead + j
            if c < 28:
                out[i, :, c] = P0[i, :, min(src, 27)]
            acc += d
            while acc >= L:
                acc -= L; src += 1
    return out


def pitch(P, R, row0=14):
    tot = P.astype(np.int64).sum((1, 2)); cum = np.cumsum(P.astype(np.int64).sum(2), 1)
    cen = np.argmax(cum * 2 >= tot[:, None], 1); out = np.zeros_like(P)
    for i in range(len(P)):
        sh = int(np.clip(row0 - cen[i], -R, R))
        if sh >= 0:
            out[i, sh:] = P[i, :28 - sh]
        else:
            out[i, :28 + sh] = P[i, -sh:]
    return out


A = cochlea_int.align_word(P0.reshape(len(P0), -1), 6).reshape(P0.shape)
V = {"align6": lambda: A, "warp16_end1/4": lambda: warp(P0, 16, 1, 4), "warp16_end1/2": lambda: warp(P0, 16, 1, 2),
     "warp12_end1/4": lambda: warp(P0, 12, 1, 4), "align6+pitch2": lambda: pitch(A, 2), "align6+pitch4": lambda: pitch(A, 4)}
names = sys.argv[2:] or list(V)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_warp.json")
res = json.load(open(out)) if os.path.exists(out) else {}
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
for name in names:
    P = V[name]().reshape(len(P0), -1); xtr, xte = P[~te], P[te]
    fes = [Features(64, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
    ctr, cte = enc(xtr), enc(xte); accs = []
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        sel = np.random.RandomState(100 * seed).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel])
        accs.append(round(float((m.predict(cte) == yte).mean()), 4))
    res[name] = {"acc": accs, "mean": round(float(np.mean(accs)), 4)}; print(name, res[name], flush=True)
    json.dump({"label": "SIMULATED (integer cochlea + floor, exact integer chip model, 3 seeds, all at once)", **res},
              open(out, "w"), indent=1)
