"""Larger margin for dreams (hw/brain/cortex_dm.py): 5 stages and all at once, exact integer model, real margin 32. spec = dmargin. 2 seeds. usage: DATA_DIR DS dmargin [...]. SIMULATED."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_dm import CortexDM
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS); ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
res = {}
for dm in [int(v) for v in sys.argv[3:]]:
    r = {}
    for sname, st in (("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]),):
        accs = []
        for seed in (1, 2):
            m = CortexDM(ctr.shape[1], dmargin=dm, night_stop=2, daydream=1, seed=seed)
            for i, s in enumerate(st):
                sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
            accs.append(float((m.predict(cte) == yte).mean()))
        r[sname] = round(float(np.mean(accs)), 4)
    res[dm] = r; print(DS, "dmargin", dm, r, flush=True)
    json.dump({"label": "SIMULATED (exact integer model, 2 seeds), real margin 32", **{str(k): v for k, v in res.items()}}, open(f"dream_margin_{DS}.json", "w"), indent=1)
