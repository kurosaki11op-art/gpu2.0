"""Onset channels for sound (cochlear-nucleus onset cells): besides the loudness picture, a picture of how much each
resonator got louder since the previous frame (rise in the integer log, subtraction only; offsets = falls). Detectors
are learned on it like any other channel. Variants: today's 10 channels + onset/offset channels (more memory), and an
equal-memory swap (3 loudness channels replaced). Integer cochlea + noise floor, exact integer chip model, 3 seeds,
all at once. usage: DATA_DIR [variant ...]"""
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
P = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8)
d = np.zeros_like(lg); d[:, :, 1:] = lg[:, :, 1:] - lg[:, :, :-1]                 # (clip, resonator, frame)
ON = np.clip(d * 32, 0, 255).reshape(len(v), -1).astype(np.uint8)                 # rise, 1 log step = 32
OFF = np.clip(-d * 32, 0, 255).reshape(len(v), -1).astype(np.uint8)
pics = {"P": (P[~te], P[te]), "ON": (ON[~te], ON[te]), "OFF": (OFF[~te], OFF[te])}
L10 = [("P", c) for c in (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))]
V = {"base10": L10,
     "base10+on2": L10 + [("ON", 31), ("ON", 95)],
     "base10+on2+off1": L10 + [("ON", 31), ("ON", 95), ("OFF", 31)],
     "swap3": [("P", c) for c in (20, 80, 140, 200, 230, ("on", 8), ("off", 8))] + [("ON", 31), ("ON", 95), ("OFF", 31)]}
names = sys.argv[2:] or list(V)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_onset.json")
res = json.load(open(out)) if os.path.exists(out) else {}
cache = {}
for name in names:
    parts_tr, parts_te = [], []
    for src, thr in V[name]:
        key = (src, str(thr))
        if key not in cache:
            xtr, xte = pics[src]
            f = Features(64, thr=thr).fit(xtr[np.isin(ytr, (0, 1))][:12000])
            enc = lambda x: np.concatenate([f.encode(x[i:i + 5000]) for i in range(0, len(x), 5000)])
            cache[key] = (enc(xtr), enc(xte))
        parts_tr.append(cache[key][0]); parts_te.append(cache[key][1])
    ctr, cte = np.concatenate(parts_tr, 1), np.concatenate(parts_te, 1); accs = []
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        sel = np.random.RandomState(100 * seed).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel])
        accs.append(round(float((m.predict(cte) == yte).mean()), 4))
    res[name] = {"code_bits": int(ctr.shape[1]), "acc": accs, "mean": round(float(np.mean(accs)), 4)}
    print(name, res[name], flush=True)
    json.dump({"label": "SIMULATED (integer cochlea + noise floor, exact integer chip model, 3 seeds, all at once)", **res},
              open(out, "w"), indent=1)
