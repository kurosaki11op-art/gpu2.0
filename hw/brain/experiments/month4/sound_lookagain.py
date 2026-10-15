"""Sound: listen more than once (LOOK AGAIN on chip). The chip learns from word-aligned pictures (word start at frame 6,
today's design); at test time it also scores the word placed at other start frames and adds the scores (PREDICT arg
1). Views: {6}, {5,6,7}, {4..8}, {5,6,6,7} (centre twice). Exact integer chip model, 3 seeds, all at once and 5 stages.
usage: DATA_DIR"""
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
P0 = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8)
P6 = cochlea_int.align_word(P0, 6); xtr = P6[~te]
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
fes = [Features(64, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
ctr = enc(xtr); views = {L: enc(cochlea_int.align_word(P0[te], L)).astype(np.int32) for L in (4, 5, 6, 7, 8)}
SETS = {"6": [6], "5,6,7": [5, 6, 7], "4..8": [4, 5, 6, 7, 8], "5,6,6,7": [5, 6, 6, 7]}
res = {}
for sname, stages in (("all_at_once", [tuple(range(10))]), ("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])):
    r = {k: [] for k in SETS}
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate(stages):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        W = m.W.T.astype(np.int32); sc = {L: views[L] @ W for L in views}
        for k, Ls in SETS.items():
            r[k].append(float((sum(sc[L] for L in Ls).argmax(1) == yte).mean()))
    res[sname] = {k: round(float(np.mean(v_)), 4) for k, v_ in r.items()}; print(sname, res[sname], flush=True)
json.dump({"label": "SIMULATED (exact integer chip model, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_lookagain.json"), "w"), indent=1)
