"""Group-structured dreams (hw/brain/cortex_group.py) vs today's dreams, 5 stages, exact integer chip model, margin 32. spec = mode:cap
(mode 0 = today's independent bits). 2 seeds. usage: DATA_DIR DS mode:cap [...]. SIMULATED."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_group import CortexGroup
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f_ = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y_, te_ = f_["y"], f_["te"]; ytr, yte = y_[~te_], y_[te_]; gF = 64
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS); gF = 32
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; res = {}
out = f"group_dreams_{DS}.json"
for spec in sys.argv[3:]:
    mode, cap = [int(v) for v in spec.split(":")]; accs = []
    for seed in (1, 2):
        m = CortexGroup(ctr.shape[1], gF=gF, cap=cap, mode=mode, night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate(stages):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
        accs.append(float((m.predict(cte) == yte).mean()))
    res[spec] = round(float(np.mean(accs)), 4); print(DS, spec, accs, flush=True)
    json.dump({"label": "SIMULATED (exact integer model, 2 seeds), 5 stages, spec = mode:cap", **res}, open(out, "w"), indent=1)
