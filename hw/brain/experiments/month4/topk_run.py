"""Slow-table chip on saved codes (CODEFILE): all at once and 5 stages, 2 seeds, single view. usage: DATA_DIR DS CODEFILE. SIMULATED."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
D, DS, CF = sys.argv[1], sys.argv[2], sys.argv[3]
z = np.load(os.path.join(D, CF)); _, ytr, _, yte = load(D, DS); ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); r = {}
for sname, stages in (("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]), ("all_at_once", [tuple(range(10))])):
    accs = []
    for seed in (1, 2):
        m = CortexSlow(ctr.shape[1], ch=500, K=3, night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate(stages):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
        accs.append(float((m.predict(cte) == yte).mean()))
    r[sname] = round(float(np.mean(accs)), 4)
print(DS, CF, "on bits", round(float(ctr.sum(1).mean()), 1), r, flush=True)
