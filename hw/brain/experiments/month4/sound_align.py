"""Align the word in time (attention locks onto the word's start): find the first frame whose loudness (sum of the
28 resonators' floored log values) passes a fraction of the clip's loudest frame, and shift the picture so that frame
lands at frame LEAD (columns shifted in, quiet filled). Integer compares and an address offset only. Then today's 10
channels x 64 detectors. Exact integer chip model, 3 seeds, all at once. usage: DATA_DIR"""
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
P0 = np.clip(255 - (top - lg) * 8, 0, 255).astype(np.uint8)                       # (clip, resonator, frame)
loud = P0.astype(np.int64).sum(1)                                                  # (clip, frame)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_align.json"); res = {}
for frac, lead in ((2, 2), (2, 4), (4, 2)):     # frac 2: threshold 3/4 of the loudest frame; frac 4: 1/2
    thr = loud.max(1, keepdims=True) * (4 - 1) >> frac if frac == 2 else loud.max(1, keepdims=True) >> 1
    start = np.argmax(loud >= thr, 1)
    P = np.zeros_like(P0)
    for i in range(len(P0)):
        sh = lead - start[i]
        if sh >= 0:
            P[i, :, sh:] = P0[i, :, :28 - sh]
        else:
            P[i, :, :28 + sh] = P0[i, :, -sh:]
    P = P.reshape(len(P), -1); xtr, xte = P[~te], P[te]
    CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
    fes = [Features(64, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
    ctr, cte = enc(xtr), enc(xte); accs = []
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        sel = np.random.RandomState(100 * seed).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel])
        accs.append(round(float((m.predict(cte) == yte).mean()), 4))
    name = f"thr{'3/4' if frac == 2 else '1/2'}_lead{lead}"
    res[name] = {"start_frame_mean": round(float(start.mean()), 2), "acc": accs, "mean": round(float(np.mean(accs)), 4)}
    print(name, res[name], flush=True)
    json.dump({"label": "SIMULATED (integer cochlea + floor, exact integer chip model, 3 seeds, all at once); today 71.9", **res},
              open(out, "w"), indent=1)
