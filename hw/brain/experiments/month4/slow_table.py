"""Redesign 6 step 1: a slow 'cortical' table that consolidates the fast table. The chip's table is trained online (perceptron-like, 5-bit,
margin rule), so its final weights reflect the last examples (order noise, about 1 point between seeds). A second table S of 8-bit entries (4
fractional bits) follows the fast table W in integer steps: after every CHUNK examples, S += (16*W - S) >> K (shift and add only). Prediction
reads S (rounded) instead of W. Same codes, exact integer chip model, all classes at once; also reports the fast table for comparison.
usage: DATA_DIR DS  chunk:K [...] ; 2 seeds. SIMULATED."""
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
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"slow_table_{DS}.json"); res = {}
cte32 = cte.astype(np.int32)
for spec in sys.argv[3:]:
    ch, K = [int(v) for v in spec.split(":")]; fa, sa = [], []
    for seed in (1, 2):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed); S = np.zeros(m.W.shape, np.int32)
        sel = np.random.RandomState(100 * seed).permutation(len(ytr))
        for i in range(0, len(sel), ch):
            b = sel[i:i + ch]; m.stage(ctr[b], ytr[b]); S += ((16 * m.W.astype(np.int32)) - S) >> K
        fa.append(float((m.predict(cte) == yte).mean())); sa.append(float(((cte32 @ S.T).argmax(1) == yte).mean()))
    res[spec] = {"fast": round(float(np.mean(fa)), 4), "slow": round(float(np.mean(sa)), 4)}; print(DS, spec, res[spec], flush=True)
    json.dump({"label": "SIMULATED (exact integer chip model + slow table, 2 seeds), spec = chunk:K", **res}, open(out, "w"), indent=1)
