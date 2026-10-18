"""One class at a time (10 stages), today's chip vs slow table (FR 3, rounding), exact integer model, margin 32, single view, 3 seeds. usage: DATA_DIR DS. SIMULATED."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
from cortex_slow import CortexSlow
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f_ = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y_, te_ = f_["y"], f_["te"]; ytr, yte = y_[~te_], y_[te_]; CHN = 100
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS); CHN = 500
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); r = {}
for name in ("today", "slow"):
    accs = []
    for seed in (1, 2, 3):
        kw = dict(night_stop=2, daydream=1, seed=seed)
        m = CortexInt(ctr.shape[1], **kw) if name == "today" else CortexSlow(ctr.shape[1], ch=CHN, K=3, **kw)
        for i in range(10):
            sel = np.where(ytr == i)[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
        accs.append(float((m.predict(cte) == yte).mean()))
    r[name] = round(float(np.mean(accs)), 4)
print(DS, "10 stages", r, flush=True)
json.dump({"label": "SIMULATED (exact integer model, margin 32, 3 seeds, single view, one class per stage)", "dataset": DS, **r}, open(f"ten_stages_slow_{DS}.json", "w"))
