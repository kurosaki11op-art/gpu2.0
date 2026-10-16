"""More test-time views (LOOK AGAIN with more shifts) - searching for variation at match time, as the research note suggests.
Images: the picture + 1-pixel shifts: v5 = centre x2 + 4 (today), v9 = centre x2 + 8 (adds diagonals), v13 = v9 + 2-pixel shifts
up/down/left/right. Words: time offsets (word start 5, 6, 7) x row shifts (-1, 0, +1 resonator rows, zero filled): t4 = today
(5,6,6,7), t3 = (5,6,7), r3 = rows -1,0,+1 at start 6 (centre x2), t3r3 = all 9 (centre x2). Scores summed (PREDICT arg 1).
Margin 32, exact integer chip model, 3 seeds, all at once and 5 stages. usage: DATA_DIR DS"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
from feature_layer import Features
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    import cochlea_int
    f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]
    ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
    v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
    lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
    P0 = np.clip(255 - (top - lg) * 8, 0, 255).astype(np.uint8)                  # (clip, row, frame)
    xtr = cochlea_int.align_word(P0[~te].reshape(-1, 784), 6)
    CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
    fes = [Features(64, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 4000]) for g in fes], 1) for i in range(0, len(x), 4000)])
    ctr = enc(xtr)

    def view(T, R):
        P = P0[te]
        if R:
            Q = np.zeros_like(P)
            if R > 0:
                Q[:, R:] = P[:, :-R]
            else:
                Q[:, :R] = P[:, -R:]
            P = Q
        return enc(cochlea_int.align_word(P.reshape(-1, 784), T)).astype(np.int32)

    V = {(T, R): view(T, R) for T in (5, 6, 7) for R in (-1, 0, 1)}
    SETS = {"t1": [(6, 0)], "t4(today)": [(5, 0), (6, 0), (6, 0), (7, 0)], "t3": [(5, 0), (6, 0), (7, 0)],
            "r3": [(6, -1), (6, 0), (6, 0), (6, 1)], "t3r3": [(T, R) for T in (5, 6, 7) for R in (-1, 0, 1)] + [(6, 0)]}
else:
    xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr = z["tr"]
    CH = (50, 150, ("on", 8), ("off", 8))
    fes = [Features(32, thr=c, pool=2).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)])
    X = xte.reshape(len(xte), 28, 28)

    def shifted(dy, dx):
        out = np.zeros_like(X); ys, yd = (slice(0, 28 - dy), slice(dy, 28)) if dy >= 0 else (slice(-dy, 28), slice(0, 28 + dy))
        xs, xd = (slice(0, 28 - dx), slice(dx, 28)) if dx >= 0 else (slice(-dx, 28), slice(0, 28 + dx))
        out[:, yd, xd] = X[:, ys, xs]; return enc(out.reshape(len(X), -1)).astype(np.int32)

    V = {(0, 0): z["te"].astype(np.int32)}
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1), (-2, 0), (2, 0), (0, -2), (0, 2)):
        V[(dy, dx)] = shifted(dy, dx)
    n4 = [(-1, 0), (1, 0), (0, -1), (0, 1)]; d4 = [(-1, -1), (-1, 1), (1, -1), (1, 1)]; t4 = [(-2, 0), (2, 0), (0, -2), (0, 2)]
    SETS = {"v1": [(0, 0)], "v5(today)": [(0, 0), (0, 0)] + n4, "v9": [(0, 0), (0, 0)] + n4 + d4, "v13": [(0, 0), (0, 0)] + n4 + d4 + t4}
res = {}
for sname, stages in (("all_at_once", [tuple(range(10))]), ("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])):
    r = {k: [] for k in SETS}
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate(stages):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        W = m.W.T.astype(np.int32); sc = {k: V[k] @ W for k in V}
        for name, ks in SETS.items():
            r[name].append(float((sum(sc[k] for k in ks).argmax(1) == yte).mean()))
    res[sname] = {k: round(float(np.mean(v_)), 4) for k, v_ in r.items()}; print(DS, sname, res[sname], flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, margin 32, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"views_more_{DS}.json"), "w"), indent=1)
