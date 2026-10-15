"""All ten classes at once (one stage), 3 seeds, exact integer chip model, month-2 rule. usage: DATA_DIR mnist|fashion"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); accs = []
for seed in (1, 2, 3):
    m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
    sel = np.random.RandomState(100 * seed).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel])
    accs.append(round(float((m.predict(cte) == yte).mean()), 4))
print(DS, "all at once", accs, "mean", round(float(np.mean(accs)), 4), flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", "acc": accs, "mean": round(float(np.mean(accs)), 4)},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"allatonce_seeds_{DS}.json"), "w"), indent=1)
