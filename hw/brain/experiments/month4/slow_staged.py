"""Slow table in staged learning (cortex_slow.py): all at once, 5 stages, 10 stages vs today's table, exact integer chip model, margin 32.
usage: DATA_DIR DS ch:K [...]; ch:K = 0:0 is today's CortexInt. 3 seeds. SIMULATED."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
from cortex_slow import CortexSlow
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f_ = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y_, te_ = f_["y"], f_["te"]; ytr, yte = y_[~te_], y_[te_]
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS)
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"slow_staged_{DS}.json"); res = {}
for spec in sys.argv[3:]:
    ch, K = [int(v) for v in spec.split(":")]; r = {}
    for sname, stages in (("all_at_once", [tuple(range(10))]), ("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])):
        accs = []
        for seed in (1, 2, 3):
            m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed) if ch == 0 else CortexSlow(ctr.shape[1], ch=ch, K=K, night_stop=2, daydream=1, seed=seed)
            for i, s in enumerate(stages):
                sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
                m.stage(ctr[sel], ytr[sel])
            accs.append(float((m.predict(cte) == yte).mean()))
        r[sname] = round(float(np.mean(accs)), 4)
    res[spec] = r; print(DS, spec, r, flush=True)
    json.dump({"label": "SIMULATED (exact integer chip model, margin 32, 3 seeds), spec = chunk:K (0:0 = today)", **res}, open(out, "w"), indent=1)
