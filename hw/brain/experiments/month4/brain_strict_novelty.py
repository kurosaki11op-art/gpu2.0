"""Novelty from inside (19 Oct 2026). SIMULATED. Train the slow-table chip on the first 4 stages (8 classes, host schedule), then show test images of the 8 known classes and of the 2 unseen ones.
The chip's own signals: best slow-table score, margin between the best two classes, and best score per active bit. Reports the AUROC of each signal for telling unseen from known (0.5 = chance, 1.0 = perfect; a higher value
means the chip can notice a new class itself), and the share of unseen examples flagged at the threshold that keeps 90 % of known examples. usage: DATA_DIR; env DS, NPS, SEEDS."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
import detector_learn
D = sys.argv[1]; DS = os.environ.get("DS", "mnist"); NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 3)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:4000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
ctr, cte = enc(xtr), enc(xte); NB = ctr.shape[1]; unseen = np.isin(yte, (8, 9))


def auroc(pos, neg):
    """probability that a random positive (unseen) scores higher than a random negative (known)"""
    r = np.argsort(np.argsort(np.concatenate([pos, neg]))) + 1; return float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


res = {"best_score": [], "margin": [], "score_per_bit": [], "flagged_at_90": []}
for seed in range(1, SEEDS + 1):
    m = CortexSlow(NB, ch=100, K=5, night_stop=2, daydream=1, seed=seed)
    for i, s in enumerate(STAGES[:4]):
        o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
    sc = cte.astype(np.int32) @ m.S.T; sc[:, ~m.known] = -(1 << 30); so = np.sort(sc, 1); best = so[:, -1]; mg = so[:, -1] - so[:, -2]; spb = best / np.maximum(cte.sum(1), 1)
    for name, v in (("best_score", best), ("margin", mg), ("score_per_bit", spb)):
        res[name].append(auroc(-v[unseen], -v[~unseen]))                  # low score / low margin = novel, so the novelty signal is -v
    thr = np.percentile(-mg[~unseen], 90); res["flagged_at_90"].append(float((-mg[unseen] > thr).mean()))
    print(DS, "seed", seed, {k: round(v[-1], 3) for k, v in res.items()}, flush=True)
out = {k: round(float(np.mean(v)), 4) for k, v in res.items()}; print(json.dumps(out)); json.dump(out, open("brain_strict_novelty_%s.json" % DS, "w"), indent=1)
