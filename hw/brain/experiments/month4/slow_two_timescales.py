"""Two slow tables with different time constants (multi-timescale consolidation, 19 Oct): same fast-table trajectory (same seed, same schedule), S_a follows with K_a, S_b with K_b;
prediction reads S_a + S_b. 2 seeds, staged and all at once, clothing / digits, single view. usage: DATA_DIR DS Ka:Kb [...]. SIMULATED."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS); ctr, cte = z["tr"], z["te"].astype(np.int32); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
for spec in sys.argv[3:]:
    ka, kb = [int(v) for v in spec.split(":")]; r = {}
    for sname, stages in (("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]), ("all_at_once", [tuple(range(10))])):
        accs = {"a": [], "b": [], "a+b": []}
        for seed in (1, 2):
            ma = CortexSlow(ctr.shape[1], ch=500, K=ka, night_stop=2, daydream=1, seed=seed); mb = CortexSlow(ctr.shape[1], ch=500, K=kb, night_stop=2, daydream=1, seed=seed)
            for i, s in enumerate(stages):
                sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
                ma.stage(ctr[sel], ytr[sel]); mb.stage(ctr[sel], ytr[sel])
            sa, sb = cte @ ma.S.T, cte @ mb.S.T
            for name, sc in (("a", sa), ("b", sb), ("a+b", sa + sb)):
                accs[name].append(float((sc.argmax(1) == yte).mean()))
        r[sname] = {k: round(float(np.mean(v)), 4) for k, v in accs.items()}
    print(DS, f"K {ka}:{kb}", r, flush=True)
