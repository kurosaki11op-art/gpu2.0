"""Dreams with lateral inhibition (cortex_wta.py) vs the slow-table chip (19 Oct 2026). SIMULATED. Same pipeline as brain_strict_digits.py (on-chip detectors, 2,000 examples per stage, 2,000 test images, 3 seeds).
Arms: slow (shipped), wta:K (night and day dreams keep at most K drawn features per spot), each as 5 stages of 2 classes ("staged") and with all classes in one stage ("once"). usage: DATA_DIR; env DS, NPS, SEEDS, ARMS."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
from cortex_wta import CortexWTA
import detector_learn
D = sys.argv[1]; DS = os.environ.get("DS", "mnist"); NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 3)); ARMS = os.environ.get("ARMS", "slow,wta:4,wta:3,wta:2").split(",")
STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
ctr, cte = enc(xtr), enc(xte); NB = ctr.shape[1]; res = {}
for arm in ARMS:
    kind, _, h = arm.partition(":"); out = {"staged": [], "once": []}
    for seed in range(1, SEEDS + 1):
        for mode in ("staged", "once"):
            m = CortexWTA(NB, kw=int(h), ch=100, K=5, night_stop=2, daydream=1, seed=seed) if kind == "wta" else CortexSlow(NB, ch=100, K=5, night_stop=2, daydream=1, seed=seed)
            groups = STAGES if mode == "staged" else [tuple(range(10))]
            for i, s in enumerate(groups):
                o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
            out[mode].append(float((m.predict(cte) == yte).mean()))
        print(DS, arm, "seed", seed, {k: round(v[-1], 4) for k, v in out.items()}, "%.0fs" % (time.time() - t0), flush=True)
    res[arm] = {k: round(float(np.mean(v)), 4) for k, v in out.items()}; json.dump(res, open("brain_strict_wta_%s.json" % DS, "w"), indent=1)
print(json.dumps(res))
