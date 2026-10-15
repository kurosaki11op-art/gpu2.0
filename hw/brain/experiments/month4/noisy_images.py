"""Images in noise: the chip learns from clean images (5 stages, month-2 rule) and is tested on test images with
salt-and-pepper noise (a fraction of the pixels set to 0 or 255, fixed seed). Receptors with and without speckle
removal (a receptor bit counts only if >= 1 of its 8 neighbours is on). Exact integer chip model, 3 seeds.
usage: DATA_DIR mnist|fashion"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import feature_layer as fl
from feature_layer import Features
from cortex_int import CortexInt
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
_orig = fl.binarize; K = 0


def supported(x, thr):
    b = _orig(x, thr)
    if K == 0 or isinstance(thr, list):
        return b
    im = b.reshape(-1, 28, 28).astype(np.int32); p = np.pad(im, ((0, 0), (1, 1), (1, 1)))
    nb = sum(p[:, 1 + dy:29 + dy, 1 + dx:29 + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx)
    return ((im == 1) & (nb >= K)).reshape(len(x), -1)


fl.binarize = supported
g = np.random.RandomState(4242); noisy = {}
for frac in (0.02, 0.05):
    x = xte.copy().reshape(len(xte), -1); m = g.random_sample(x.shape) < frac
    x[m] = np.where(g.random_sample(m.sum()) < 0.5, 0, 255).astype(x.dtype); noisy[f"sp{int(frac * 100)}%"] = x
res = {}
for k in (0, 1):
    K = k
    fes = [Features(32, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 2000]) for f in fes], 1) for i in range(0, len(x), 2000)])
    ctr = enc(xtr); tests = {"clean": enc(xte), **{n: enc(v) for n, v in noisy.items()}}
    accs = {n: [] for n in tests}
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        for n, c in tests.items():
            accs[n].append(float((m.predict(c) == yte).mean()))
    res[f"despeckle{k}"] = {n: round(float(np.mean(v)), 4) for n, v in accs.items()}
    print(DS, "speckle removal" if k else "no speckle removal", res[f"despeckle{k}"], flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"noisy_images_{DS}.json"), "w"), indent=1)
