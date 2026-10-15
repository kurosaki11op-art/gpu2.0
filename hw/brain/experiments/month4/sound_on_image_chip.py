"""Sound on the Tang Nano's image chip: sound pictures (integer cochlea + noise floor, computed on the PC) encoded with
the image encoder's fixed receptors (brightness > 50, > 150, ON / OFF cells) and 32 detectors per channel learned from
stage-1 sound pictures -> 4,608-bit code, the image chip's memory. Exact integer chip model, month-2 rule, 3 seeds.
Compared with the full sound chip (10 channels x 64 detectors, 23,040 bits). usage: DATA_DIR"""
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
P = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8); xtr, xte = P[~te], P[te]
res = {}
for name, CH, F in (("image_chip_4x32", (50, 150, ("on", 8), ("off", 8)), 32),
                    ("image_chip_4x32_soundthr", (110, 200, ("on", 8), ("off", 8)), 32)):
    fes = [Features(F, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
    ctr, cte = enc(xtr), enc(xte); accs = []
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        accs.append(round(float((m.predict(cte) == yte).mean()), 4))
    res[name] = {"acc": accs, "mean": round(float(np.mean(accs)), 4), "bits": int(ctr.shape[1])}; print(name, res[name], flush=True)
json.dump({"label": "SIMULATED (exact integer chip model, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_on_image_chip.json"), "w"), indent=1)
