"""Integer multi-prototype dreams (hw/brain/cortex_proto.py) vs today's dreams: 5 stages (and all at once), 3 seeds, margin 32,
exact integer model. K = 1 (single counter set, structure of today's), 2, 4, 8. usage: DATA_DIR DS [K ...]"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
from cortex_proto import CortexProto
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f_ = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y_, te_ = f_["y"], f_["te"]; ytr, yte = y_[~te_], y_[te_]
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS)
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
Ks = [int(k) for k in sys.argv[3:]] or [0, 2, 4, 8]                       # 0 = today's CortexInt
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"proto_dreams_{DS}.json"); res = {}
for K in Ks:
    r = {}
    for sname, stages in (("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]), ("all_at_once", [tuple(range(10))])):
        accs = []
        for seed in (1, 2, 3):
            m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed) if K == 0 else CortexProto(ctr.shape[1], protos=K, night_stop=2, daydream=1, seed=seed)
            for i, s in enumerate(stages):
                sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
                m.stage(ctr[sel], ytr[sel])
            accs.append(float((m.predict(cte) == yte).mean()))
        r[sname] = round(float(np.mean(accs)), 4)
    r["dream_memory_bits"] = int(m.memory_bits()["dream_counts"]); res[f"K{K}"] = r; print(DS, f"K={K}", r, flush=True)
    json.dump({"dataset": DS, "label": "SIMULATED (exact integer model, margin 32, 3 seeds)", **res}, open(out, "w"), indent=1)
