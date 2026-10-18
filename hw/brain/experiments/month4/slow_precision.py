"""Slow table precision: FR fractional bits and round-to-nearest in the follow step, staged (5 stages) and all at once, exact integer model, 3 seeds.
usage: DATA_DIR DS FR:rnd [...]. SIMULATED. (FR 1, no rounding = the first RTL version; floor-shift bias stalls S below W by up to 7 / 2^FR.)"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS); ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
res = {}
for spec in sys.argv[3:]:
    fr, rnd = [int(v) for v in spec.split(":")]; r = {}
    for sname, stages in (("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]), ("all_at_once", [tuple(range(10))])):
        accs = []
        for seed in (1, 2, 3):
            m = CortexSlow(ctr.shape[1], ch=500, K=3, FR=fr, rnd=rnd, night_stop=2, daydream=1, seed=seed)
            for i, s in enumerate(stages):
                sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
            accs.append(float((m.predict(cte) == yte).mean()))
        r[sname] = round(float(np.mean(accs)), 4)
    res[spec] = r; print(DS, "FR:rnd", spec, r, flush=True)
    json.dump({"label": "SIMULATED (exact integer model, margin 32, 3 seeds, single view), spec = FR:round", **res}, open(f"slow_precision_{DS}.json", "w"), indent=1)
