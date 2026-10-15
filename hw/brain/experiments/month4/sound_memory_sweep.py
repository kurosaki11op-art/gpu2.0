"""Shrinking the sound chip's memory: fewer detectors per channel (F) and fewer brightness channels, same integer
cochlea + noise floor, same encoder kinds. Core memory (and the SRAM macro count) scales with the code bits
(channels x F x 36 positions). Exact integer chip model, month-2 rule, 3 seeds; all at once and 5 stages.
usage: DATA_DIR [config ...]  config = name:F:channels, channels comma-separated thresholds plus on/off
e.g. f32:32:20,50,80,110,140,170,200,230,on,off"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea_int
from feature_layer import Features
from cortex_int import CortexInt
D = sys.argv[1]
z = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = z["S"], z["y"], z["te"]
ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
P = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8); xtr, xte = P[~te], P[te]
ALL = "20,50,80,110,140,170,200,230,on,off"
cfgs = sys.argv[2:] or ["f64:64:" + ALL, "f32:32:" + ALL, "f16:16:" + ALL, "ch5_f64:64:50,110,170,230,on",
                        "ch6_f32:32:20,80,140,200,on,off"]
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_memory_sweep.json")
res = json.load(open(out)) if os.path.exists(out) else {}
for cfg in cfgs:
    name, F, chs = cfg.split(":"); F = int(F)
    CH = [(c, 8) if c in ("on", "off") else int(c) for c in chs.split(",")]
    fes = [Features(F, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
    ctr, cte = enc(xtr), enc(xte); r = {"F": F, "channels": chs, "code_bits": int(ctr.shape[1])}
    for sname, stages in (("all_at_once", [tuple(range(10))]), ("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])):
        accs = []
        for seed in (1, 2, 3):
            m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
            for i, s in enumerate(stages):
                sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
                m.stage(ctr[sel], ytr[sel])
            accs.append(round(float((m.predict(cte) == yte).mean()), 4))
        r[sname] = {"acc": accs, "mean": round(float(np.mean(accs)), 4)}
    res[name] = r; print(name, r, flush=True)
    json.dump({"label": "SIMULATED (integer cochlea + noise floor, exact integer chip model, 3 seeds)", **res}, open(out, "w"), indent=1)
