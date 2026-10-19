"""Prototype dreams with pruned dream memory (19 Oct 2026). SIMULATED. Prototype dreams (K = 4 count sets per class, cortex_proto_slow.py) lifted staged clothing for 4x the dream memory; synaptic pruning of the dream counts
(zero a count whose bit on-rate is below 1/DIV, after each stage) is tested as a way to buy that back. Arms: slow (shipped, K = 1), slowp:DIV (K = 1 with pruned dream counts), proto:K:DIV (K prototypes, DIV 0 = no pruning).
Reports staged accuracy (5 stages of 2 classes) and the fraction of dream counts left nonzero (ESTIMATED memory: nonzero count x its bits, ignoring indices). Same pipeline as brain_strict_digits.py. usage: DATA_DIR; env DS, NPS, SEEDS, ARMS."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
from cortex_proto_slow import CortexProtoSlow
import detector_learn
D = sys.argv[1]; DS = os.environ.get("DS", "mnist"); NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 3)); ARMS = os.environ.get("ARMS", "slow,slowp:16,proto:4:0,proto:4:16,proto:4:8,proto:4:4").split(",")
STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
ctr, cte = enc(xtr), enc(xte); NB = ctr.shape[1]; res = {}
for arm in ARMS:
    kind, *p = arm.split(":"); acc = []; nz = []
    for seed in range(1, SEEDS + 1):
        if kind == "proto":
            K, DIV = int(p[0]), int(p[1]); m = CortexProtoSlow(NB, protos=K, ch=100, K=5, night_stop=2, daydream=1, seed=seed)
        else:
            DIV = int(p[0]) if p else 0; m = CortexSlow(NB, ch=100, K=5, night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate(STAGES):
            o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
            if DIV:
                if kind == "proto": m.onp[(m.onp.astype(np.int64) * DIV) < m.nprot[:, None]] = 0
                else: m.on[(m.on.astype(np.int64) * DIV) < m.n[:, None]] = 0
        acc.append(float((m.predict(cte) == yte).mean())); a = m.onp if kind == "proto" else m.on; nz.append(float((a > 0).mean()))
    res[arm] = {"staged": round(float(np.mean(acc)), 4), "dream_counts_nonzero": round(float(np.mean(nz)), 4)}; print(DS, arm, res[arm], "%.0fs" % (time.time() - t0), flush=True)
    json.dump(res, open("brain_strict_proto_%s.json" % DS, "w"), indent=1)
