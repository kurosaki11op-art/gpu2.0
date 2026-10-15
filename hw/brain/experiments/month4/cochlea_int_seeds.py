"""3 seeds (example order + random lanes), month-2 rule, sound codes from the float vs the integer cochlea. usage: DATA_DIR"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea
from cortex_int import CortexInt
D = sys.argv[1]
_, ytr, _, yte = cochlea.load_speech(os.path.join(D, "speech"), os.path.join(D, "speech_pics_res.npz"), cochlea.sound_picture_res)
ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); res = {}
for name, f in (("float", "sep_speech_F64_p2.npz"), ("integer", "sep_speech_int_F64_p2.npz")):
    z = np.load(os.path.join(D, f)); ctr, cte = z["tr"], z["te"]; accs = []
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        accs.append(round(float((m.predict(cte) == yte).mean()), 4))
    res[name] = {"acc": accs, "mean": round(float(np.mean(accs)), 4)}; print(name, res[name], flush=True)
json.dump({"label": "SIMULATED (exact integer chip model, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cochlea_int_seeds.json"), "w"), indent=1)
