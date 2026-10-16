"""Pool-limited multi-prototype dreams (hw/brain/cortex_proto_pool.py): 5 stages, 3 seeds, margin 32, exact integer model.
usage: DATA_DIR DS POOL:T [POOL:T ...]   (T = spawn threshold in sixteenths)"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_proto_pool import CortexPool
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f_ = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y_, te_ = f_["y"], f_["te"]; ytr, yte = y_[~te_], y_[te_]
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS)
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"proto_pool_{DS}.json"); res = {}
for spec in sys.argv[3:]:
    P, T = [int(v) for v in spec.split(":")]; accs = []; used = []
    for seed in (1, 2, 3):
        m = CortexPool(ctr.shape[1], pool=P, spawn=T, night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        accs.append(float((m.predict(cte) == yte).mean())); used.append(int(m.pool_used[0]))
    r = {"5_stages": round(float(np.mean(accs)), 4), "slots_used": float(np.mean(used)),
         "dream_memory_bits": int(m.memory_bits()["dream_counts"])}
    res[spec] = r; print(DS, spec, r, flush=True)
    json.dump({"dataset": DS, "label": "SIMULATED (exact integer model, margin 32, 3 seeds)", **res}, open(out, "w"), indent=1)
