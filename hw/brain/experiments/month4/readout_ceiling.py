"""Is the chip's readout (5-bit table, one pass, margin rule) what limits all-at-once accuracy? Same codes, exact integer chip model, all classes at
once, varying the number of passes over the real training set (a 'second day') and the table width (cmax 15 = 5 bit, 31, 63) and margin.
usage: DATA_DIR DS  [cmax:passes:margin ...]. 2 seeds. SIMULATED."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS); ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"readout_ceiling_{DS}.json"); res = {}
for spec in sys.argv[3:]:
    cm, ps, mg = [int(v) for v in spec.split(":")]; accs = []
    for seed in (1, 2):
        m = CortexInt(ctr.shape[1], cmax=cm, margin=mg, night_stop=2, daydream=1, seed=seed)
        for p in range(ps):
            sel = np.random.RandomState(100 * seed + p).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel])
        accs.append(float((m.predict(cte) == yte).mean()))
    res[spec] = round(float(np.mean(accs)), 4); print(DS, spec, accs, flush=True)
    json.dump({"label": "SIMULATED (exact integer chip model, 2 seeds), spec = cmax:passes:margin", **res}, open(out, "w"), indent=1)
