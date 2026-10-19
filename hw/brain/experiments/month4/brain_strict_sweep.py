"""One-knob-at-a-time sweep of the slow-table chip around its default (19 Oct 2026), staged (5 stages of 2 classes) and all-at-once, on-chip detectors, 2,000 examples per stage. SIMULATED.
Knobs: ndream (dreams per old class per stage), night (night passes), daydream, margin, cmax, ch (ticks between slow-table follow steps), K (slow-table time constant shift).
usage: DATA_DIR; env DS, NPS, SEEDS (default 2), ENC (base|s1 encoder), GRID (1 = one knob at a time, 2 = margin x ndream x night combinations). One line per setting; the default is `default`."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
import detector_learn, feature_layer
ENC = os.environ.get("ENC", "base"); GRIDSEL = os.environ.get("GRID", "1")
D = sys.argv[1]; DS = os.environ.get("DS", "mnist"); NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 2)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
if ENC == "s1": feature_layer.PS, feature_layer.ST = 5, 1
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
if ENC == "s1":
    for f in fes: f.pool = 4
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
ctr, cte = enc(xtr), enc(xte); NB = ctr.shape[1]
DEF = dict(ch=100, K=5, night_stop=2, daydream=1, ndream=6000, night=2, margin=32, cmax=15)
GRID = [("default", {})] + [(f"{k}={v}", {k: v}) for k, vs in (("ndream", (1500, 3000, 12000, 24000)), ("night", (1, 4)), ("daydream", (0, 3, 6)), ("margin", (8, 16, 64, 128)), ("cmax", (7, 31)), ("ch", (25, 50, 200, 500)), ("K", (3, 4, 6, 7))) for v in vs]
GRID2 = [("default", {})] + [(f"margin={mg} ndream={nd} night={nt}", dict(margin=mg, ndream=nd, night=nt)) for mg in (128, 256, 512, 1024) for nd, nt in ((6000, 2), (1500, 2), (1500, 1))]
if GRIDSEL == "2": GRID = GRID2
res = {}
for name, kw in GRID:
    cfg = dict(DEF, **kw); out = {"staged": [], "once": []}
    for seed in range(1, SEEDS + 1):
        for mode in ("staged", "once"):
            m = CortexSlow(NB, seed=seed, **cfg)
            for i, s in enumerate(STAGES if mode == "staged" else [tuple(range(10))]):
                o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
            out[mode].append(float((m.predict(cte) == yte).mean()))
    res[name] = {k: round(float(np.mean(v)), 4) for k, v in out.items()}; print(DS, name, res[name], "%.0fs" % (time.time() - t0), flush=True)
    json.dump(res, open("brain_strict_sweep_%s_%s_g%s.json" % (DS, ENC, GRIDSEL), "w"), indent=1)
