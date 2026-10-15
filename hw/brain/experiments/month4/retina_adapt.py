"""Retinal adaptation for images: the brightness receptors' thresholds follow each image's brightest pixel
(thr' = (max * thr) >> 8, a shift-add with constant thr) instead of being fixed at 50 / 150; ON/OFF cells unchanged.
Same detector learning, exact integer chip model, month-2 rule, 3 seeds, after 5 stages. usage: DATA_DIR mnist|fashion"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import feature_layer as fl
from feature_layer import Features
from cortex_int import CortexInt
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
_orig = fl.binarize


def adapted(x, thr):
    if isinstance(thr, tuple) and thr[0] == "adapt":
        mx = x.reshape(len(x), -1).max(1).astype(np.int64)[:, None]
        return x.reshape(len(x), -1).astype(np.int64) > ((mx * thr[1]) >> 8)
    return _orig(x, thr)


fl.binarize = adapted
res = {}
for name, CH in (("fixed", (50, 150, ("on", 8), ("off", 8))), ("adapt", (("adapt", 50), ("adapt", 150), ("on", 8), ("off", 8)))):
    if name == "fixed":
        z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
    else:
        fes = [Features(32, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
        enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 2000]) for f in fes], 1) for i in range(0, len(x), 2000)])
        ctr, cte = enc(xtr), enc(xte)
    accs = []
    for seed in range(1, int(os.environ.get("SEEDS", "3")) + 1):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate(stages):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        accs.append(round(float((m.predict(cte) == yte).mean()), 4))
    res[name] = {"acc": accs, "mean": round(float(np.mean(accs)), 4)}; print(DS, name, res[name], "%.0fs" % (time.time() - t0), flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"retina_adapt_{DS}_s{os.environ.get('SEEDS', '3')}.json"), "w"), indent=1)
