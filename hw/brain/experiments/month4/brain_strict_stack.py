"""Stack the partial wins on the same chip (19 Oct 2026). SIMULATED. Four chips, on-chip learned detectors, slow table (K = 5), 5 stages of 2 classes ("staged") and all classes in one stage ("once"):
  base      shipped chip: stride-2 detectors, 2 x 2 pooling, one dream-count set per class
  proto4    + prototype dreams (4 dream-count sets per class, cortex_proto_slow.py): about 4x the dream memory
  s1        + stride-1 detectors with 4 x 4 pooling (same 4,608-bit code, finer winner grid): the ENC_S1 encoder option
  s1proto4  both
Each arm prints staged and all-at-once accuracy and the memory the chip's counters need (bits). Same data pipeline as brain_strict_digits.py. usage: DATA_DIR; env DS (mnist|fashion), NPS, SEEDS, ARMS."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import feature_layer
from cortex_core import load
from cortex_slow import CortexSlow
from cortex_proto_slow import CortexProtoSlow
import detector_learn
D = sys.argv[1]; DS = os.environ.get("DS", "mnist"); NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 3)); ARMS = os.environ.get("ARMS", "base,proto4,s1,s1proto4").split(",")
STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]; CODES = {}


def codes(enc):
    """codes of the train and test images with the stride-2 (base) or stride-1 (s1) encoder; the detectors are learned on the chip's own rule from the first stage's images"""
    if enc not in CODES:
        feature_layer.PS, feature_layer.ST = (5, 1) if enc == "s1" else (5, 2)
        fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
        if enc == "s1":
            for f in fes: f.pool = 4
        e = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
        CODES[enc] = (e(xtr), e(xte)); print("codes", enc, CODES[enc][0].shape, "%.0fs" % (time.time() - t0), flush=True)
    return CODES[enc]


res = {}
for arm in ARMS:
    enc = "s1" if arm.startswith("s1") else "base"; proto = arm.endswith("proto4"); ctr, cte = codes(enc); NB = ctr.shape[1]; out = {"staged": [], "once": []}
    for seed in range(1, SEEDS + 1):
        for mode in ("staged", "once"):
            m = CortexProtoSlow(NB, protos=4, ch=100, K=5, night_stop=2, daydream=1, seed=seed) if proto else CortexSlow(NB, ch=100, K=5, night_stop=2, daydream=1, seed=seed)
            for i, s in enumerate(STAGES if mode == "staged" else [tuple(range(10))]):
                o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
            out[mode].append(float((m.predict(cte) == yte).mean()))
        print(DS, arm, "seed", seed, {k: round(v[-1], 4) for k, v in out.items()}, "%.0fs" % (time.time() - t0), flush=True)
    res[arm] = {k: round(float(np.mean(v)), 4) for k, v in out.items()}; res[arm]["memory_bits"] = dict(m.memory_bits(), slow_table=int(m.S.size * 8)); res[arm]["memory_kbytes"] = round(sum(res[arm]["memory_bits"].values()) / 8 / 1024, 1); print(DS, arm, res[arm], flush=True)
    json.dump(res, open("brain_strict_stack_%s.json" % DS, "w"), indent=1)
print(json.dumps({k: {m: v[m] for m in ("staged", "once")} for k, v in res.items()}))
