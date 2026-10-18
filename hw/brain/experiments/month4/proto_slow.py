"""Multi-prototype dreams + slow table (hw/brain/cortex_proto_slow.py) vs slow table alone vs today, 5 stages and all at once, exact integer model, margin 32,
single view. spec = K (prototypes; 0 = slow table alone via CortexSlow, -1 = today). 3 seeds. usage: DATA_DIR DS K [...]. SIMULATED."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
from cortex_slow import CortexSlow
from cortex_proto_slow import CortexProtoSlow
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f_ = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y_, te_ = f_["y"], f_["te"]; ytr, yte = y_[~te_], y_[te_]; CHN = 100
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS); CHN = 500
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
res = {}; out = f"proto_slow_{DS}.json"
for K in [int(v) for v in sys.argv[3:]]:
    r = {}
    for sname, stages in (("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]), ("all_at_once", [tuple(range(10))])):
        accs = []
        for seed in (1, 2, 3):
            kw = dict(night_stop=2, daydream=1, seed=seed)
            m = CortexInt(ctr.shape[1], **kw) if K < 0 else CortexSlow(ctr.shape[1], ch=CHN, K=3, **kw) if K == 0 else CortexProtoSlow(ctr.shape[1], protos=K, ch=CHN, K=3, **kw)
            for i, s in enumerate(stages):
                sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
            accs.append(float((m.predict(cte) == yte).mean()))
        r[sname] = round(float(np.mean(accs)), 4)
    res[f"K{K}"] = r; print(DS, f"K={K}", r, flush=True)
    json.dump({"label": "SIMULATED (exact integer model, margin 32, 3 seeds, single view); K -1 = today, 0 = slow table alone, >0 = prototypes + slow table", **res}, open(out, "w"), indent=1)
