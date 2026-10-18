"""Redesign 8 step 1: homeostatic bias (intrinsic plasticity). Staged learning leaves the table with a recency bias (staged_diag.py, recency_bias.py:
an oracle bias on recent classes gives +3.5). On chip, each class keeps a bias b_c (small integer, subtracted from its score) and a running prediction rate
r_c (EMA, shift only). Every decision: r_c += ((c == pred) * 1024 - r_c) >> E; then b_c += S if r_c > target_c, b_c -= S if r_c < target_c, clipped to +-BMAX.
target_c = the class's share of the training examples (the chip's own counters n_c; here equal). No labels at inference. 1-2 seeds, the test stream in random order.
Caveat: assumes deployment class mix is like the training mix. usage: DATA_DIR DS. SIMULATED."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f_ = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y_, te_ = f_["y"], f_["te"]; ytr, yte = y_[~te_], y_[te_]
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS)
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; res = {}


def stream(sc, y, S, E, BMAX, order, target):
    b = np.zeros(10, np.int64); r = np.zeros(10, np.int64); ok = 0
    for i in order:
        p = int(np.argmax(sc[i] - b)); ok += (p == y[i])
        r += ((np.arange(10) == p) * 1024 - r) >> E
        b += np.where(r > target, S, np.where(r < target, -S, 0)); b = np.clip(b, -BMAX, BMAX)
    return ok / len(order)


cfgs = [(1, 7, 400), (2, 7, 400), (4, 7, 800), (2, 9, 400), (4, 9, 800), (8, 9, 800)]
for sname, st in (("5_stages", stages), ("all", [tuple(range(10))])):
    for seed in (1, 2):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate(st):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
        sc = cte.astype(np.int32) @ m.W.T.astype(np.int32); order = np.random.RandomState(7 + seed).permutation(len(yte))
        res.setdefault(f"{sname}|plain", []).append(float((sc.argmax(1) == yte).mean()))
        for (S, E, BM) in cfgs:
            res.setdefault(f"{sname}|S{S}_E{E}_B{BM}", []).append(float(stream(sc, yte, S, E, BM, order, 1024 // 10)))
    for k in [k for k in res if k.startswith(sname)]: print(k, round(float(np.mean(res[k])), 4), flush=True)
json.dump({"label": "SIMULATED (exact integer model, 2 seeds, test stream order random)", **{k: round(float(np.mean(v)), 4) for k, v in res.items()}}, open(f"homeostasis_{DS}.json", "w"), indent=1)
