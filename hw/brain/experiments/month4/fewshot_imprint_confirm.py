"""Confirm the few-shot fix inside the chip model: CortexInt(imprint=4) runs IMPRINT for each new class at the end of
its stage (novelty-gated prototype imprint, only while the class has seen <= 8 examples). Setting: the chip knows
classes 0-4 (all their examples), then learns 5-9 from k examples each. 5 seeds; k = 1, 2, 5, 10, 20; base vs
imprint; accuracy on old, new and all classes. Sound uses the aligned codes (sep_speech_align_F64_p2.npz).
usage: DATA_DIR DS"""
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
old_te, new_te = yte < 5, yte >= 5
RULE = dict(B=10, night=2, daydream=1, night_stop=2)
res = {}
for k in (1, 2, 5, 10, 20):
    rows = {}
    for s in (1, 2, 3, 4, 5):
        g = np.random.RandomState(1000 * s)
        so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
        sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
        for name, imp in (("base", 0), ("imprint", 4)):
            m = CortexInt(ctr.shape[1], seed=s, imprint=imp, **RULE); m.stage(ctr[so], ytr[so]); m.stage(ctr[sn], ytr[sn])
            p = m.predict(cte) == yte
            rows.setdefault(name, []).append({"old": float(p[old_te].mean()), "new": float(p[new_te].mean()), "all": float(p.mean())})
    res[k] = {n: {key: round(float(np.mean([r[key] for r in v])), 4) for key in ("old", "new", "all")} for n, v in rows.items()}
    print(DS, "k", k, res[k], flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 5 seeds)", "results": res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"fewshot_imprint_confirm_{DS}.json"), "w"), indent=1)
