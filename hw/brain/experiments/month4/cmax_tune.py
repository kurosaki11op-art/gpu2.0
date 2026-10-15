"""Table counter range (cmax; today 15 = 5-bit signed) with margin 32 / 64 on clothing and words, 3 seeds, all at once and
5 stages. cmax 31 needs a 6-bit table (+20% table memory). Exact integer chip model. usage: DATA_DIR DS"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y, te = f["y"], f["te"]; ytr, yte = y[~te], y[te]
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS)
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"cmax_tune_{DS}.json"); res = {}
for cmax, margin in ((7, 16), (15, 32), (31, 32), (31, 64), (63, 64)):
    r = {}
    for sname, stages in (("all_at_once", [tuple(range(10))]), ("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])):
        accs = []
        for seed in (1, 2, 3):
            m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed, cmax=cmax, margin=margin)
            for i, s in enumerate(stages):
                sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
                m.stage(ctr[sel], ytr[sel])
            accs.append(float((m.predict(cte) == yte).mean()))
        r[sname] = round(float(np.mean(accs)), 4)
    res[f"cmax{cmax}_margin{margin}"] = r; print(DS, f"cmax {cmax} margin {margin}", r, flush=True)
    json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", **res}, open(out, "w"), indent=1)
