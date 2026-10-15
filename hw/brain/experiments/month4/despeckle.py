"""Image noise removal by lateral support: a receptor bit (brightness or ON / OFF cell) counts only if at least K of
its 8 neighbours in the same channel are also on (isolated speckles are dropped). Integer counts and compares only.
Same detector learning, exact integer chip model, month-2 rule, 3 seeds. usage: DATA_DIR mnist|fashion"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import feature_layer as fl
from feature_layer import Features
from cortex_int import CortexInt
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
_orig = fl.binarize
K = 0


def supported(x, thr):
    b = _orig(x, thr)
    if K == 0 or isinstance(thr, list):
        return b
    im = b.reshape(-1, 28, 28).astype(np.int32); p = np.pad(im, ((0, 0), (1, 1), (1, 1)))
    nb = sum(p[:, 1 + dy:29 + dy, 1 + dx:29 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    return ((im == 1) & (nb >= K)).reshape(len(x), -1)


fl.binarize = supported
res = {}
for k in [int(v) for v in os.environ.get("KS", "0,1,2").split(",")]:
    K = k
    if k == 0:
        z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
    else:
        fes = [Features(32, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
        enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 2000]) for f in fes], 1) for i in range(0, len(x), 2000)])
        ctr, cte = enc(xtr), enc(xte)
    accs = []
    for seed in range(1, int(os.environ.get("SEEDS", "3")) + 1):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        accs.append(round(float((m.predict(cte) == yte).mean()), 4))
    res[f"support{k}"] = {"acc": accs, "mean": round(float(np.mean(accs)), 4)}; print(DS, f"support>={k}", res[f"support{k}"], flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"despeckle_{DS}_s{os.environ.get('SEEDS', '3')}.json"), "w"), indent=1)
