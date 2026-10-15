"""Images: look more than once at test time (small eye movements). The trained chip scores the test image and copies
shifted by one pixel (up / down / left / right) and adds the table scores; the class with the largest sum wins. Same
learning, 5x the decision work. Encoders rebuilt exactly as hw/brain/experiments/month2/m2f.py (checked against the
cached codes). Exact integer chip model, 3 seeds, all at once and 5 stages. usage: DATA_DIR DS"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from feature_layer import Features
from cortex_int import CortexInt
D, DS = sys.argv[1], sys.argv[2]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
CH = (50, 150, ("on", 8), ("off", 8))
fes = [Features(32, thr=c, pool=2).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
same = bool((enc(xte[:500]) == cte[:500]).all()); print("encoder rebuilt exactly:", same, flush=True)
X = xte.reshape(len(xte), 28, 28)


def shifted(dy, dx):
    out = np.zeros_like(X); ys, yd = (slice(0, 28 - dy), slice(dy, 28)) if dy >= 0 else (slice(-dy, 28), slice(0, 28 + dy))
    xs, xd = (slice(0, 28 - dx), slice(dx, 28)) if dx >= 0 else (slice(-dx, 28), slice(0, 28 + dx))
    out[:, yd, xd] = X[:, ys, xs]; return enc(out.reshape(len(X), -1)).astype(np.int32)


views = {"centre": cte.astype(np.int32)}
for name, (dy, dx) in {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}.items():
    views[name] = shifted(dy, dx)
res = {"encoder_exact": same}
for sname, stages in (("all_at_once", [tuple(range(10))]), ("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])):
    r = {"centre": [], "5_views": [], "5_views_centre_x2": []}
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate(stages):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        W = m.W.T.astype(np.int32); sc = {k: v @ W for k, v in views.items()}
        tot = sum(sc.values())
        r["centre"].append(float((sc["centre"].argmax(1) == yte).mean()))
        r["5_views"].append(float((tot.argmax(1) == yte).mean()))
        r["5_views_centre_x2"].append(float(((tot + sc["centre"]).argmax(1) == yte).mean()))
    res[sname] = {k: round(float(np.mean(v)), 4) for k, v in r.items()}; print(DS, sname, res[sname], flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"image_saccades_test_{DS}.json"), "w"), indent=1)
