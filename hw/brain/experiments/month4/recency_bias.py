"""Oracle test of the recency bias in staged learning: train 5 stages (exact integer model, today's rule), then subtract beta from the score of the classes
of the last stage (and beta/2 for the stage before, etc. 'ramp') before the argmax. If accuracy rises a lot, the table over-scores recent real-trained classes
and a per-class bias (10 small integers) could calibrate it. Also reports the mean score of REAL test images of each class on its own row vs the mean score
of DREAMS of that class on its own row. 1-2 seeds. usage: DATA_DIR DS. SIMULATED diagnostic."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt, _dream
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS); ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; age = np.zeros(10)
for i, s in enumerate(stages):
    for c in s: age[c] = 4 - i          # 0 = last stage
res = {}; rows = []
for seed in (1, 2):
    m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
    for i, s in enumerate(stages):
        sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
    sc = cte.astype(np.int32) @ m.W.T.astype(np.int32)
    real = np.array([sc[yte == c, c].mean() for c in range(10)])
    buf = np.zeros(ctr.shape[1], np.int32); dr = []
    for c in range(10):
        v = []
        for _ in range(300):
            k = _dream(m.on, m.n, c, m.rng, buf); v.append(m.W[c, buf[:k]].astype(np.int32).sum())
        dr.append(np.mean(v))
    rows.append((real, np.array(dr), sc))
    for a in (0.25, 0.5, 1, 1.5, 2):
        dv = np.array(dr); bias = a * (dv - dv.mean()); p = (sc - bias[None, :]).argmax(1); res.setdefault(f'dreamnorm_{a}', []).append(float((p == yte).mean()))
    for beta in (0, 80, 160, 320, 640):
        for name, bias in (("last", np.where(age == 0, beta, 0)), ("ramp", beta * np.maximum(0, 3 - age) / 3.0)):
            p = (sc - bias[None, :]).argmax(1)
            res.setdefault(f"{name}_{beta}", []).append(float((p == yte).mean()))
print("mean own-row score, real test images vs dreams (seed 1), by stage age (0 = last):")
real, dr, _ = rows[0]
for a in range(5):
    cs = np.where(age == a)[0]; print(f"  age {a}: real {real[cs].mean():8.1f}  dream {dr[cs].mean():8.1f}")
for k, v in res.items(): print(k, round(float(np.mean(v)), 4))
json.dump({"label": "SIMULATED diagnostic (exact integer model, 2 seeds)", **{k: round(float(np.mean(v)), 4) for k, v in res.items()}}, open(f"recency_bias_{DS}.json", "w"), indent=1)
