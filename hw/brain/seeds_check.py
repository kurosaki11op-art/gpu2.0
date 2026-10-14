"""Spread over seeds for the month-2 rule on the integer chip model: the order of arriving examples and the random
lanes change with the seed (sensory detectors fixed). usage: python seeds_check.py DATA_DIR mnist|fashion|speech"""
import json, os, sys
import numpy as np
from cortex_int import CortexInt
from cortex_core import load

D, DS = sys.argv[1], sys.argv[2]
F = 64 if DS == "speech" else 32
z = np.load(os.path.join(D, f"sep_{DS}_F{F}_p2.npz")); ctr, cte = z["tr"], z["te"]
if DS == "speech":
    import cochlea
    _, ytr, _, yte = cochlea.load_speech(os.path.join(D, "speech"), os.path.join(D, "speech_pics_res.npz"), cochlea.sound_picture_res)
else:
    _, ytr, _, yte = load(D, DS)
ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
res = []
for seed in (1, 2, 3):
    m = CortexInt(ctr.shape[1], B=10, night=2, daydream=1, night_stop=2, seed=seed)
    for i, s in enumerate(stages):
        sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
        m.stage(ctr[sel], ytr[sel])
    res.append(float((m.predict(cte) == yte).mean())); print(DS, "seed", seed, res[-1], flush=True)
out = {"dataset": DS, "label": "SIMULATED (integer chip model)", "after_5_stages": res,
       "mean": float(np.mean(res)), "min": float(np.min(res)), "max": float(np.max(res))}
print(out)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", f"cortex_seeds_{DS}.json"), "w"), indent=1)
