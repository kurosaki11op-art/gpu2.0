"""More receptor types for images: brightness receptors at (30, 100, 170) instead of (50, 150), ON/OFF cells unchanged
(5 channels, 5,760-bit code, +25% memory). Same detector learning, exact integer chip model, month-2 rule, 3 seeds.
usage: DATA_DIR mnist|fashion"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from feature_layer import Features
from cortex_int import CortexInt
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
res = {}
for name, CH in (("50_150", None), ("30_100_170", (30, 100, 170, ("on", 8), ("off", 8)))):
    if CH is None:
        z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
    else:
        fes = [Features(32, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
        enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 2000]) for f in fes], 1) for i in range(0, len(x), 2000)])
        ctr, cte = enc(xtr), enc(xte)
    accs = []
    for seed in [int(v) for v in os.environ.get("SEEDLIST", "1,2,3").split(",")]:
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        accs.append(round(float((m.predict(cte) == yte).mean()), 4))
    res[name] = {"acc": accs, "mean": round(float(np.mean(accs)), 4), "bits": int(ctr.shape[1])}; print(DS, name, res[name], flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"receptor_types_{DS}{os.environ.get('TAG', '')}.json"), "w"), indent=1)
