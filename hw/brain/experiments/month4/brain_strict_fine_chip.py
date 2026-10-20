"""Fine code on the chip (20 Oct 2026), SIMULATED. Replace the shipped coarse code (5x5 patches, stride 2, pool 2: 4,608 bits) by the fine code (3x3 patches, stride 1, pool 3: 8,192 bits; same on-chip detector rule, first stage's images only), or use both. Chip: margin 256 / 1,500 dreams / 1 night, 3 seeds, one pass and 5 stages.
Also reports the mean number of active bits per image (reads per decision). usage: DATA_DIR; env DS, NPS."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import feature_layer, detector_learn
from feature_layer import Features, patches, binarize
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); NPS = int(os.environ.get("NPS", 2000)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]; first = xtr[np.isin(ytr, STAGES[0])]
enc = lambda fs, x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fs], 1) for i in range(0, len(x), 1000)])
fc = detector_learn.learn_features(first); c_tr, c_te = enc(fc, xtr), enc(fc, xte)


def learn_fine(x, F=32, chans=(50, 150, ("on", 8), ("off", 8)), nb=9, pool=3):
    out = []
    for c in chans:
        sd = detector_learn.StreamDetectors(F, nb=nb); pp, _ = patches(binarize(x, c)); sd.learn(pp); sd.reseed()
        f = Features(F, thr=c); f.cnt = sd.cnt.copy(); f.pool = pool; out.append(f)
    return out


feature_layer.PS, feature_layer.ST = 3, 1; ff = learn_fine(first); f_tr, f_te = enc(ff, xtr), enc(ff, xte); feature_layer.PS, feature_layer.ST = 5, 2
CODES = {"coarse (shipped)": (c_tr, c_te), "fine 3x3": (f_tr, f_te), "coarse + fine": (np.concatenate([c_tr, f_tr], 1), np.concatenate([c_te, f_te], 1))}


def run(ctr, cte, staged, seed):
    m = CortexSlow(ctr.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)
    for i, s in enumerate(STAGES if staged else [tuple(range(10))]):
        o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
    return float((m.predict(cte) == yte).mean())


for name, (a, b) in CODES.items():
    r = {k: round(float(np.mean([run(a, b, k == "staged", s) for s in (1, 2, 3)])), 4) for k in ("once", "staged")}
    print(DS, name, a.shape[1], "bits, active per image %.0f" % a.sum(1).mean(), r, "%.0fs" % (time.time() - t0), flush=True)
