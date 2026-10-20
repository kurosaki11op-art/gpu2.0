"""Isolate the staged loss (20 Oct 2026), SIMULATED, clothing, coarse code, margin 256 / 1,500 dreams / 1 night, 3 seeds.
  once          all examples interleaved in one pass (reference 86.5)
  blocked       the same single pass but the examples arrive class by class (stage order), NO dreams, NO night (what order alone does to the table)
  blocked+real  stages as usual but each night replays ALL earlier real examples (upper bound of any replay fix)
  staged        shipped
usage: DATA_DIR; env DS."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
ctr, cte = enc(xtr), enc(xte)
mk = lambda s, **k: CortexSlow(ctr.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=s, margin=256, ndream=1500, night=1, **k)
res = {}
for s in (1, 2, 3):
    perm = lambda o, i: o[np.random.RandomState(100 * s + i).permutation(len(o))]
    m = mk(s); m.stage(ctr[perm(np.arange(len(ytr)), 0)], ytr[perm(np.arange(len(ytr)), 0)]); res.setdefault("once", []).append((m.predict(cte) == yte).mean())
    m = mk(s, ); m.ndream = 0; m.night = 0                                                      # blocked, no dreams and no night
    for i, st in enumerate(STAGES): o = perm(np.where(np.isin(ytr, st))[0], i); m.stage(ctr[o], ytr[o])
    res.setdefault("blocked (no replay)", []).append((m.predict(cte) == yte).mean())
    m = mk(s)
    for i, st in enumerate(STAGES): o = perm(np.where(np.isin(ytr, st))[0], i); m.stage(ctr[o], ytr[o])
    res.setdefault("staged (shipped)", []).append((m.predict(cte) == yte).mean())
    m = mk(s)                                                                                    # staged, each stage re-presents ALL earlier real examples too (upper bound for replay)
    for i, st in enumerate(STAGES):
        o = perm(np.where(np.isin(ytr, sum(STAGES[:i + 1], ())))[0], i); m.stage(ctr[o], ytr[o])
    res.setdefault("replay all earlier real data", []).append((m.predict(cte) == yte).mean())
for k, v in res.items(): print(DS, k, round(float(np.mean(v)), 4), flush=True)
