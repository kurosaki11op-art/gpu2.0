"""10 learning stages of one class each, 3 seeds (example order + random lanes), exact integer chip model, month-2
rule. Sound uses the chip's integer cochlea with the noise floor. usage: DATA_DIR mnist|fashion|speech"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_floor_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y, te = f["y"], f["te"]; ytr, yte = y[~te], y[te]
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS)
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); accs = []
for seed in (1, 2, 3):
    m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
    for c in range(10):
        sel = np.where(ytr == c)[0]; sel = sel[np.random.RandomState(100 * seed + c).permutation(len(sel))]
        m.stage(ctr[sel], ytr[sel])
    accs.append(round(float((m.predict(cte) == yte).mean()), 4))
print(DS, "10 one-class stages", accs, "mean", round(float(np.mean(accs)), 4), flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", "acc": accs, "mean": round(float(np.mean(accs)), 4)},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"stages10_seeds_{DS}.json"), "w"), indent=1)
