"""Closing the clothing gap (research ideas for weightless classifiers). Baseline = today's encoder (4 channels: brightness 50 /
150, ON8, OFF8; F = 32, pool 2) with margin 32. Variants (single view, 3 seeds, all at once and 5 stages, exact integer chip model):
  quant3      : brightness thresholds at the 25 / 50 / 75 % points of the nonzero training pixels (histogram quantiles, learned
                once by counting), 3 brightness channels
  quant2      : two quantile thresholds (33 / 66 %) replacing 50 / 150 (same memory as today)
  coarse      : today + a coarse centre-surround pair (ON5 / OFF5: pixel vs the mean of its 5x5 neighbourhood > 8), +2 channels
  ens2        : two tables with different encoders (today's, and quant2 + coarse), scores summed (2x memory)
usage: DATA_DIR"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from feature_layer import Features
from cortex_int import CortexInt
D = sys.argv[1]
xtr, ytr, xte, yte = load(D, "fashion"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
xtr = xtr.reshape(len(xtr), -1); xte = xte.reshape(len(xte), -1)


def coarse(x):
    """ON5 / OFF5 planes as uint8 images: 128 + (pixel - mean of the 5x5 neighbourhood) clipped (box sum, integer //25)"""
    im = x.reshape(-1, 28, 28).astype(np.int32); p = np.pad(im, ((0, 0), (2, 2), (2, 2)), mode="edge"); s = np.zeros_like(im)
    for dy in range(5):
        for dx in range(5):
            s += p[:, dy:dy + 28, dx:dx + 28]
    d = im - s // 25
    return np.clip(128 + d, 0, 255).astype(np.uint8).reshape(len(x), -1), np.clip(128 - d, 0, 255).astype(np.uint8).reshape(len(x), -1)


nz = xtr[xtr > 0]; q = lambda ps: [int(np.percentile(nz, p)) for p in ps]
print("quantile thresholds 25/50/75:", q((25, 50, 75)), "33/66:", q((33, 66)), flush=True)
on5_tr, off5_tr = coarse(xtr); on5_te, off5_te = coarse(xte)
sel = np.isin(ytr, (0, 1))
planes = {"x": (xtr, xte), "on5": (on5_tr, on5_te), "off5": (off5_tr, off5_te)}


def build(spec):
    """spec: list of (plane, thr) -> codes (train, test)"""
    tr, te_ = [], []
    for plane, thr in spec:
        a, b = planes[plane]; f = Features(32, thr=thr, pool=2).fit(a[sel][:12000])
        enc = lambda x: np.concatenate([f.encode(x[i:i + 5000]) for i in range(0, len(x), 5000)])
        tr.append(enc(a)); te_.append(enc(b))
    return np.concatenate(tr, 1), np.concatenate(te_, 1)


BASE = [("x", 50), ("x", 150), ("x", ("on", 8)), ("x", ("off", 8))]
SPECS = {"base": BASE,
         "quant3": [("x", t) for t in q((25, 50, 75))] + BASE[2:],
         "quant2": [("x", t) for t in q((33, 66))] + BASE[2:],
         "coarse": BASE + [("on5", 8), ("off5", 8)]}
codes = {n: build(s) for n, s in SPECS.items()}; print("encoded", flush=True)
codes["quant2+coarse"] = build([("x", t) for t in q((33, 66))] + BASE[2:] + [("on5", 8), ("off5", 8)])


def run(names):
    out = {}
    for sname, stages in (("all_at_once", [tuple(range(10))]), ("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])):
        accs = []
        for seed in (1, 2, 3):
            tot = 0
            for n in names:
                ctr, cte = codes[n]; m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
                for i, s in enumerate(stages):
                    idx = np.where(np.isin(ytr, s))[0]; idx = idx[np.random.RandomState(100 * seed + i).permutation(len(idx))]
                    m.stage(ctr[idx], ytr[idx])
                tot = tot + cte.astype(np.int32) @ m.W.T.astype(np.int32)
            accs.append(float((tot.argmax(1) == yte).mean()))
        out[sname] = round(float(np.mean(accs)), 4)
    return out


res = {}
for label, names in (("base", ["base"]), ("quant2", ["quant2"]), ("quant3", ["quant3"]), ("coarse", ["coarse"]),
                     ("quant2+coarse", ["quant2+coarse"]), ("ens2(base+quant2+coarse)", ["base", "quant2+coarse"])):
    r = run(names); r["code_bits"] = [int(codes[n][0].shape[1]) for n in names]; res[label] = r; print(label, r, flush=True)
    json.dump({"label": "SIMULATED (exact integer chip model, margin 32, 3 seeds, single view)", **res},
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "clothing_gap.json"), "w"), indent=1)
