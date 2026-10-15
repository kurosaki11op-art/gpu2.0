"""Accuracy vs dream budget (learning energy is ~95% dreams). Exact integer chip model, 5 stages, month-2 rule except
ndream (dreams per old class per stage and per night pass) and night passes. Energy per learned example from the
layout (pipelined core: LEARN 2,465 cycles, DREAM 7,109; 0.70-0.98 nJ per cycle). usage: DATA_DIR mnist|fashion"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
out = []
for ndream, night in ((6000, 2), (3000, 2), (6000, 1), (3000, 1), (1500, 1), (750, 1)):
    m = CortexInt(ctr.shape[1], ndream=ndream, night=night, night_stop=2, daydream=1); day = 0
    for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
        sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(i).permutation(len(sel))]
        old = int(m.known.sum()); m.stage(ctr[sel], ytr[sel]); day += len(sel) + ndream * old
    acc = float((m.predict(cte) == yte).mean()); cyc = (60000 * 2465 + (day + int(m.stats[0])) * 7109) / 60000
    r = {"ndream": ndream, "night": night, "acc": round(acc, 4), "dreams_per_example": round((day + int(m.stats[0])) / 60000, 2),
         "uJ_per_example": [round(cyc * e / 1000, 1) for e in (0.70, 0.98)]}
    out.append(r); print(DS, r, flush=True)
json.dump({"dataset": DS, "label": "SIMULATED accuracy, ESTIMATED energy", "runs": out},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"dream_budget_{DS}.json"), "w"), indent=1)
