"""Novelty from view agreement (19 Oct 2026). SIMULATED. Same set-up as brain_strict_novelty.py (train on 8 digits in 4 stages, test known 0-7 against unseen 8-9), but with eye-movement signals: each test image is also seen
shifted one pixel (4 views). Signals (higher = more novel), each reported as AUROC for unseen against known:
  margin        top-2 margin of the centre view (the earlier signal)
  disagree      number of the 4 shifted views whose top class differs from the centre view's
  min_margin    smallest top-2 margin over the 5 views
  mean_margin   mean top-2 margin over the 5 views
  combo         -(mean margin) + 40 x disagreement (integer-like mix, constant picked by hand and not tuned on the test)
and, for the best signal, the share of unseen flagged at the threshold that keeps 90 % of known. usage: DATA_DIR; env DS, NPS, SEEDS."""
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
ctr = enc(xtr); X = xte.reshape(len(xte), 28, 28); views = [enc(xte)]
for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
    out = np.zeros_like(X); ys, yd = (slice(0, 28 - dy), slice(dy, 28)) if dy >= 0 else (slice(-dy, 28), slice(0, 28 + dy)); xs, xd = (slice(0, 28 - dx), slice(dx, 28)) if dx >= 0 else (slice(-dx, 28), slice(0, 28 + dx))
    out[:, yd, xd] = X[:, ys, xs]; views.append(enc(out.reshape(len(X), -1)))
NB = ctr.shape[1]; unseen = np.isin(yte, (8, 9))


def auroc(pos, neg):
    r = np.argsort(np.argsort(np.concatenate([pos, neg]))) + 1; return float((r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


res = {}
for seed in range(1, SEEDS + 1):
    m = CortexSlow(NB, ch=100, K=5, night_stop=2, daydream=1, seed=seed)
    for i, s in enumerate(STAGES[:4]):
        o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
    pr, mg = [], []
    for v in views:
        sc = v.astype(np.int32) @ m.S.T; sc[:, ~m.known] = -(1 << 30); so = np.sort(sc, 1); pr.append(sc.argmax(1)); mg.append(so[:, -1] - so[:, -2])
    pr, mg = np.array(pr), np.array(mg); disagree = (pr[1:] != pr[0]).sum(0); sig = {"margin": -mg[0], "disagree": disagree.astype(float), "min_margin": -mg.min(0), "mean_margin": -mg.mean(0), "combo": -mg.mean(0) + 40.0 * disagree}
    for k, v in sig.items(): res.setdefault(k, []).append(auroc(v[unseen], v[~unseen]))
    best = sig["combo"]; thr = np.percentile(best[~unseen], 90); res.setdefault("combo_flagged_at_90", []).append(float((best[unseen] > thr).mean()))
    print("seed", seed, {k: round(v[-1], 3) for k, v in res.items()}, flush=True)
out = {k: round(float(np.mean(v)), 4) for k, v in res.items()}; print(json.dumps(out)); json.dump(out, open("brain_strict_novelty2_%s.json" % DS, "w"), indent=1)
