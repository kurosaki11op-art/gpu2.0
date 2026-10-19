"""Synaptic pruning test (19 Oct 2026). Train the slow-table chip (K = 5, ch = 100, on-chip detectors, 5 stages of 2 classes, host schedule as the shipped path), then after the last night zero every slow-table
synapse whose magnitude is below a threshold (|S| < T in the table's 8-bit units, 8 units = 1 fast-table step) and read accuracy. Reports the fraction of synapses kept (the memory a sparse store would need,
ESTIMATED from the count, not a layout). Brain principle: synaptic pruning. SIMULATED. usage: DATA_DIR; env DS (mnist|fashion), NPS, SEEDS."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
import detector_learn
D = sys.argv[1]; DS = os.environ.get("DS", "mnist"); NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 2)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
ctr, cte = enc(xtr), enc(xte); NB = ctr.shape[1]; res = {}
for seed in range(1, SEEDS + 1):
    m = CortexSlow(NB, ch=100, K=5, night_stop=2, daydream=1, seed=seed)
    for i, s in enumerate(STAGES):
        o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
    S0 = m.S.copy()
    for T in (0, 4, 8, 12, 16, 24, 32):
        m.S[:] = np.where(np.abs(S0) < T, 0, S0); keep = float((m.S != 0).mean()); a = float((m.predict(cte) == yte).mean())
        res.setdefault(T, []).append((a, keep)); print(DS, "seed", seed, "T", T, "acc", round(a, 4), "kept", round(keep, 4), flush=True)
out = {T: {"acc": round(float(np.mean([a for a, _ in v])), 4), "kept": round(float(np.mean([k for _, k in v])), 4)} for T, v in res.items()}
print(json.dumps(out)); json.dump(out, open("brain_strict_prune_%s.json" % DS, "w"), indent=1)
