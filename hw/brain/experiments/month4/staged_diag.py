"""What limits staged learning? Clothing, 5 stages of 2 classes, exact integer chip model (today's rule), seeds 1-2. Reports (1) per-class
accuracy staged vs all at once, (2) accuracy on the classes of each stage after the last stage, (3) the mean table row mass (sum of |W|) per
class, to look for recency bias, (4) the confusion of stage-1 classes with stage-5 classes. usage: DATA_DIR DS. SIMULATED diagnostic."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS); ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; out = {}
for name, st in (("staged", stages), ("all", [tuple(range(10))])):
    pc = np.zeros(10); mass = np.zeros(10); conf = np.zeros((10, 10))
    for seed in (1, 2):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate(st):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
        p = m.predict(cte)
        for c in range(10):
            pc[c] += (p[yte == c] == c).mean() / 2; mass[c] += np.abs(m.W[c]).sum() / 2
            for q in range(10): conf[c, q] += (p[yte == c] == q).mean() / 2
    out[name] = {"per_class": np.round(pc, 3).tolist(), "row_mass": np.round(mass).tolist(), "confusion": np.round(conf, 2).tolist()}
    print(name, "acc", round(float(pc.mean()), 4)); print(" per class", np.round(pc, 3)); print(" row mass", np.round(mass))
d = np.array(out["all"]["per_class"]) - np.array(out["staged"]["per_class"])
print("loss per class (all - staged)", np.round(d, 3)); print("loss by stage", [round(float(d[list(s)].mean()), 3) for s in stages])
cs = np.array(out["staged"]["confusion"]); ca = np.array(out["all"]["confusion"]); ds = (cs - ca); np.fill_diagonal(ds, 0)
print("largest increases in confusion (true -> predicted, staged - all):")
idx = np.dstack(np.unravel_index(np.argsort(-ds.ravel())[:8], ds.shape))[0]
for a, b in idx: print(f"  {a}->{b}: +{ds[a, b]:.3f}")
json.dump({"label": "SIMULATED diagnostic (exact integer model, 2 seeds)", **out}, open(f"staged_diag_{DS}.json", "w"), indent=1)
