"""Our own learning rules (cortex_rules.py), 20 Oct 2026. SIMULATED, on-chip detectors, 2,000 examples per stage, 5 stages of 2 classes (staged) and all in one stage (once), 3 seeds, chip settings from env MARGIN / NDREAM / NIGHT.
Arms: base (shipped rule), split (control: night as its own call, must equal base), grade:SH (graded surprise), budget:X (synaptic budget, X in 1/16 units), shy:1 (night downscaling). A rule is kept only if clothing staged beats the plateau (about 84.5)
and digits do not drop. usage: DATA_DIR; env DS, NPS, SEEDS, ARMS."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
from cortex_rules import CortexRules
import detector_learn
D = sys.argv[1]; DS = os.environ.get("DS", "mnist"); NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 3)); t0 = time.time()
ARMS = os.environ.get("ARMS", "base,split,grade:5,grade:6,grade:7,grade:8,budget:0,budget:1,budget:2,budget:4,shy:1").split(",")
CFG = dict(margin=int(os.environ.get('MARGIN', 32)), ndream=int(os.environ.get('NDREAM', 6000)), night=int(os.environ.get('NIGHT', 2))); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
ctr, cte = enc(xtr), enc(xte); NB = ctr.shape[1]; res = {}
for arm in ARMS:
    rule, _, par = arm.partition(":"); out = {"staged": [], "once": []}
    for seed in range(1, SEEDS + 1):
        for mode in ("staged", "once"):
            m = CortexSlow(NB, ch=100, K=int(os.environ.get('KSLOW', 5)), night_stop=2, daydream=1, seed=seed, **CFG) if rule == "base" else CortexRules(NB, rule=rule, par=int(par or 0), ch=100, K=int(os.environ.get("KSLOW", 5)), night_stop=int(os.environ.get("NSTOP", 2)), daydream=1, seed=seed, **CFG)
            for i, s in enumerate(STAGES if mode == "staged" else [tuple(range(10))]):
                o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
            out[mode].append(float((m.predict(cte) == yte).mean()))
    res[arm] = {k: round(float(np.mean(v)), 4) for k, v in out.items()}; print(DS, arm, res[arm], "%.0fs" % (time.time() - t0), flush=True)
    json.dump(res, open("brain_strict_rules_%s.json" % DS, "w"), indent=1)
