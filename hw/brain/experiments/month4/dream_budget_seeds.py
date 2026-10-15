"""3-seed check of the cheaper dream budget (ndream 1500, one night pass) against the month-2 rule (6000, two passes).
Seeds change the example order and the chip's random lanes. Exact integer model, 5 stages. usage: DATA_DIR mnist|fashion|speech"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
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
ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); N = len(ytr)
res = {}
for ndream, night in ((6000, 2), (1500, 1)):
    accs, dpe = [], []
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], ndream=ndream, night=night, night_stop=2, daydream=1, seed=seed); day = 0
        for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            old = int(m.known.sum()); m.stage(ctr[sel], ytr[sel]); day += len(sel) + ndream * old
        accs.append(float((m.predict(cte) == yte).mean())); dpe.append((day + int(m.stats[0])) / N)
    res[f"{ndream}x{night}"] = {"acc": [round(a, 4) for a in accs], "mean": round(float(np.mean(accs)), 4),
                                "dreams_per_example": round(float(np.mean(dpe)), 2)}
    print(DS, ndream, night, res[f"{ndream}x{night}"], flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"dream_budget_seeds_{DS}.json"), "w"), indent=1)
