"""Confirm the slow table (cortex_slow.py) all at once with 5 seeds: today's CortexInt vs CortexSlow, single view, margin 32. usage: DATA_DIR DS ch K. SIMULATED."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
from cortex_slow import CortexSlow
D, DS, ch, K = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f_ = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y_, te_ = f_["y"], f_["te"]; ytr, yte = y_[~te_], y_[te_]
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS)
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
res = {"today": [], "slow": []}
for seed in (1, 2, 3, 4, 5):
    sel = np.random.RandomState(100 * seed).permutation(len(ytr))
    for name, m in (("today", CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)), ("slow", CortexSlow(ctr.shape[1], ch=ch, K=K, night_stop=2, daydream=1, seed=seed))):
        m.stage(ctr[sel], ytr[sel]); res[name].append(float((m.predict(cte) == yte).mean()))
    print(DS, seed, res["today"][-1], res["slow"][-1], flush=True)
out = {"label": f"SIMULATED (exact integer chip model, margin 32, 5 seeds, all at once, single view), ch {ch}, K {K}", "dataset": DS,
       **{k: {"acc": [round(a, 4) for a in v], "mean": round(float(np.mean(v)), 4)} for k, v in res.items()}}
print(DS, "today", out["today"]["mean"], "slow", out["slow"]["mean"])
json.dump(out, open(f"slow_confirm_{DS}.json", "w"), indent=1)
