"""Multi-scale vote (19-20 Oct 2026). SIMULATED. Two chips learn the same data with different encoders (base: stride-2 detectors with 2 x 2 pooling; s1: stride-1 detectors with 4 x 4 pooling), and at test their slow-table scores are added
(adds only, 2x the memory; brain principle: several cortical areas with different receptive fields vote). Optional third chip with a differently seeded base encoder (arm 3). Reports each chip alone and the vote, staged (5 stages of 2 classes) and all at once.
Chip settings from env MARGIN / NDREAM / NIGHT (recommended 256 / 1,500 / 1). usage: DATA_DIR; env DS, NPS, SEEDS."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import feature_layer
from cortex_core import load
from cortex_slow import CortexSlow
import detector_learn
D = sys.argv[1]; DS = os.environ.get("DS", "mnist"); NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 3)); t0 = time.time()
CFG = dict(margin=int(os.environ.get('MARGIN', 32)), ndream=int(os.environ.get('NDREAM', 6000)), night=int(os.environ.get('NIGHT', 2))); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]


def codes(kind):
    feature_layer.PS, feature_layer.ST = (5, 1) if kind == "s1" else (5, 2)
    first = xtr[np.isin(ytr, STAGES[0])]
    if kind == "base2": first = first[np.random.RandomState(11).permutation(len(first))[::-1]][: len(first) // 2]            # a differently fitted base encoder: another half of the first day, other order
    fes = detector_learn.learn_features(first)
    if kind == "s1":
        for f in fes: f.pool = 4
    e = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
    return e(xtr), e(xte)


KINDS = ["base", "s1", "base2"]; C = {k: codes(k) for k in KINDS}; print("codes ready %.0fs" % (time.time() - t0), flush=True)
res = {}
for mode in ("staged", "once"):
    out = {k: [] for k in ("base", "s1", "base2", "base+s1", "base+s1+base2")}
    for seed in range(1, SEEDS + 1):
        ms = {}
        for k in KINDS:
            m = CortexSlow(C[k][0].shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed, **CFG)
            for i, s in enumerate(STAGES if mode == "staged" else [tuple(range(10))]):
                o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(C[k][0][o], ytr[o])
            ms[k] = m
        sc = {k: C[k][1].astype(np.int32) @ ms[k].S.T for k in KINDS}
        for k in KINDS: sc[k][:, ~ms[k].known] = -(1 << 28)
        for name, parts in (("base", ["base"]), ("s1", ["s1"]), ("base2", ["base2"]), ("base+s1", ["base", "s1"]), ("base+s1+base2", KINDS)):
            out[name].append(float((sum(sc[k] for k in parts).argmax(1) == yte).mean()))
        print(DS, mode, "seed", seed, {k: round(v[-1], 4) for k, v in out.items()}, "%.0fs" % (time.time() - t0), flush=True)
    res[mode] = {k: round(float(np.mean(v)), 4) for k, v in out.items()}; print(DS, mode, res[mode], flush=True)
json.dump(res, open("brain_strict_ens_%s.json" % DS, "w"), indent=1)
