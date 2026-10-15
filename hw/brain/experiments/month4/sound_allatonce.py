"""Sound with the chip's integer cochlea + noise floor: all words at once (one stage) and 5 stages, exact integer chip
model, month-2 rule, 3 seeds. Saves the codes as sep_speech_floor_F64_p2.npz in DATA_DIR. usage: DATA_DIR"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea_int
from feature_layer import Features
from cortex_int import CortexInt
D = sys.argv[1]; cache = os.path.join(D, "sep_speech_floor_F64_p2.npz")
z = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = z["S"], z["y"], z["te"]
ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
if os.path.exists(cache):
    c = np.load(cache); ctr, cte = c["tr"], c["te"]
else:
    v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
    lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
    P = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8); xtr, xte = P[~te], P[te]
    CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
    fes = [Features(64, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
    ctr, cte = enc(xtr), enc(xte); np.savez_compressed(cache, tr=ctr, te=cte)
res = {}
for name, stages in (("all_at_once", [tuple(range(10))]), ("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])):
    accs = []
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate(stages):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        accs.append(round(float((m.predict(cte) == yte).mean()), 4))
    res[name] = {"acc": accs, "mean": round(float(np.mean(accs)), 4)}; print(name, res[name], flush=True)
json.dump({"label": "SIMULATED (integer cochlea + noise floor, exact integer chip model, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_allatonce.json"), "w"), indent=1)
