"""Hand-over instead of merge: chip A learns 0-4 (one stage), its whole memory is copied into chip B, and B then learns
5-9 as its own stage (sequential transfer, no table addition). Compared with the parallel merge in merge_seeds.py: chip A learns 0-4, chip B learns 5-9 (each one stage, month-2 rule); their
memories are added (table clipped to +-15, counters and counts added, halved if full) into a third chip, which then
sleeps one self-regulated night. Same procedure as hw/brain/month2_final.py; seeds change example orders and random
lanes. Exact integer chip model. usage: DATA_DIR mnist|fashion|speech"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt, _dream, _practise
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_floor_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y, te = f["y"], f["te"]; ytr, yte = y[~te], y[te]
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS)
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); NB = ctr.shape[1]
RULE = dict(B=10, night=2, daydream=1, night_stop=2); res = []
import copy
for s in (1, 2, 3):
    order = lambda sel, k: sel[np.random.RandomState(1000 * s + k).permutation(len(sel))]
    A = CortexInt(NB, seed=10 * s + 1, **RULE); sa = order(np.where(ytr < 5)[0], 11); A.stage(ctr[sa], ytr[sa])
    B = copy.deepcopy(A)
    sb = order(np.where(ytr >= 5)[0], 12); B.stage(ctr[sb], ytr[sb])
    res.append({"handover": round(float((B.predict(cte) == yte).mean()), 4)})
    print(DS, "seed", s, res[-1], flush=True)
mean = round(float(np.mean([r["handover"] for r in res])), 4)
print(DS, "hand-over mean", mean, flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", "runs": res, "mean": mean},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"merge_handover_{DS}.json"), "w"), indent=1)
