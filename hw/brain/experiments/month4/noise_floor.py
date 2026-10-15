"""Noise floor in the cochlea (auditory adaptation): per resonator channel, a floor estimated from the clip's quietest
frames is subtracted from every frame sum before the integer log. Variants: none (current), min (quietest frame),
low4 (mean of the 4 quietest frames, sum >> 2), low4x2 (twice that). Integer cochlea, same detector learning, exact
integer chip model, month-2 rule, 3 seeds. usage: DATA_DIR [modes, e.g. low4x3,low8x2]"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea, cochlea_int
from feature_layer import Features
from cortex_int import CortexInt
D = sys.argv[1]; root = os.path.join(D, "speech"); t0 = time.time()
cache = os.path.join(D, "speech_framesums_int.npz")
if os.path.exists(cache):
    z = np.load(cache); S, y, te = z["S"], z["y"], z["te"]
else:
    test = set(open(os.path.join(root, "testing_list.txt")).read().split()); S, y, te = [], [], []
    for c, w in enumerate(cochlea.WORDS):
        fs = sorted(os.listdir(os.path.join(root, w))); X = np.stack([cochlea.read(os.path.join(root, w, f)) for f in fs])
        for i in range(0, len(X), 1000):
            S.append(cochlea_int._bank(X[i:i + 1000].astype(np.int16).astype(np.int64), cochlea_int.A1, cochlea_int.A2,
                                       cochlea_int.G, cochlea.FR, cochlea_int.FB).astype(np.int32))
        y += [c] * len(fs); te += [f"{w}/{f}" in test for f in fs]
    S = np.concatenate(S); y = np.array(y); te = np.array(te); np.savez_compressed(cache, S=S, y=y, te=te)
print("frame sums", S.shape, "%.0fs" % (time.time() - t0), flush=True)


def picture(S, mode):
    v = S.astype(np.int64)
    if mode != "none":
        srt = np.sort(v, 2)
        if mode == "min":
            fl = srt[:, :, :1]
        elif mode.startswith("low8"):
            fl = srt[:, :, :8].sum(2, keepdims=True) >> 3
        else:
            fl = srt[:, :, :4].sum(2, keepdims=True) >> 2
        if "x" in mode:
            fl = fl * int(mode.split("x")[1])
        v = v - fl
    v = np.maximum(v, 1); e = np.floor(np.log2(v)).astype(np.int64)
    lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
    return np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8)


CH, F = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)), 64
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
res = {}
for mode in (sys.argv[2].split(",") if len(sys.argv) > 2 else ("none", "min", "low4", "low4x2")):
    P = picture(S, mode); xtr, xte = P[~te], P[te]
    fes = [Features(F, thr=c).fit(xtr[np.isin(ytr, stages[0])][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
    ctr, cte = enc(xtr), enc(xte); accs = []
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate(stages):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        accs.append(round(float((m.predict(cte) == yte).mean()), 4))
    res[mode] = {"acc": accs, "mean": round(float(np.mean(accs)), 4)}
    print(mode, res[mode], "%.0fs" % (time.time() - t0), flush=True)
json.dump({"label": "SIMULATED (integer cochlea, exact integer chip model, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "noise_floor%s.json" % ("_" + sys.argv[2].replace(",", "_") if len(sys.argv) > 2 else "")), "w"), indent=1)
