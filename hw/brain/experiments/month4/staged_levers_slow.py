"""Staged clothing, quick levers on the recency bias / dream-vs-real mismatch (exact integer model, 2 seeds): daydream count, margin, night dreams.
usage: DATA_DIR DS key=value[,key=value] ...  (keys: daydream, margin, ndream, night). SIMULATED."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow as CortexInt
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS); ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; res = {}
for spec in sys.argv[3:]:
    kw = dict(night_stop=2, daydream=1); kw.update({k: int(v) for k, v in (p.split("=") for p in spec.split(","))}); accs = []
    for seed in (1, 2):
        m = CortexInt(ctr.shape[1], seed=seed, ch=500, K=3, **kw)
        for i, s in enumerate(stages):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
        accs.append(float((m.predict(cte) == yte).mean()))
    res[spec] = round(float(np.mean(accs)), 4); print(DS, spec, accs, flush=True)
json.dump({"label": "SIMULATED (exact integer model, 2 seeds), 5 stages", **res}, open(f"staged_levers_slow_{DS}.json", "w"), indent=1)
