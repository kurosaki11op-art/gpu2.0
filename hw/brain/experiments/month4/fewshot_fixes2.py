"""Round 2 of fixes for "a new class from a few examples is outvoted after shipping" (research note:
docs/research/fewshot_class_incremental.md). The chip learns classes 0-4 from all their examples (one stage), then
5-9 from k examples each (second stage, month-2 rule). Then, on the same trained chip, variants of the readout / write:
  base        : table only (today)
  imprint W0  : one-shot imprint (C-FSCIL mode 1 / weight imprinting / novelty gating): each new example adds
                step = W0 >> floor(log2 n) (n = its index in the class, at least 1) on its active bits (clipped at 15)
  align       : per-class norm alignment (Weight Aligning, integer form): class score << s_c, s_c = floor(log2(Nmax/N_c))
                with N_c = sum |W_c| (capped at 4)
  ROUND 2 (round 1 showed: a plain imprint fixes k=1 but swamps the old classes for k >= 5; hippocampus scores
  added to the table pulled new classes down):
  proto W0    : prototype imprint - a new class's row is raised to its MEAN code times W0: W[c,b] = max(W[c,b],
                (on[c,b] * W0) >> log2(n_c)) with n_c a power of two of its examples (shift only) - the write cannot grow
                with the number of examples
  gate T      : hippocampus gate - if the best stored episode of a new class overlaps the input on more than T/8 of
                the episode's bits, answer that class; otherwise the table answers
  (old) hippocampus gating (complementary learning systems): new classes also score their best stored episode,
                overlap - popcount/2, shifted left by s, added to the table score
All integer: adds, shifts, compares. Exact integer chip model, 3 seeds. usage: DATA_DIR DS"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
RULE = dict(B=10, night=2, daydream=1, night_stop=2); NEW = np.arange(5, 10)
old_te, new_te = yte < 5, yte >= 5
X = cte.astype(np.int32)


def split(pred):
    return {"old": float((pred == yte)[old_te].mean()), "new": float((pred == yte)[new_te].mean()), "all": float((pred == yte).mean())}


def scores(W, known):
    s = (X @ W.T.astype(np.int32)).astype(np.int64); s[:, ~known] = -(1 << 40); return s


def align(s, W):
    N = np.abs(W.astype(np.int64)).sum(1); N = np.maximum(N, 1)
    sh = np.clip(np.floor(np.log2(N.max() / N)), 0, 4).astype(np.int64)
    return s << sh[None]


res = {}
for k in (1, 5, 20):
    rows = {}
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s)
        so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
        sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in NEW]); sn = sn[g.permutation(len(sn))]
        m = CortexInt(ctr.shape[1], seed=s, **RULE); m.stage(ctr[so], ytr[so]); m.stage(ctr[sn], ytr[sn])
        base = scores(m.W, m.known); rows.setdefault("base", []).append(split(base.argmax(1)))
        sh = int(np.floor(np.log2(k)))
        for W0 in (4, 6, 8, 12):
            W = m.W.astype(np.int16).copy()
            for c in NEW:
                cnt = sum(ctr[i].astype(np.int64) for i in sn if ytr[i] == c)
                W[c] = np.maximum(W[c], np.minimum((cnt * W0) >> sh, 15))
            rows.setdefault(f"proto{W0}", []).append(split(scores(W, m.known).argmax(1)))
        E = ctr[sn].astype(np.int32); Ey = ytr[sn]; pop = E.sum(1)
        ov = X @ E.T
        best = ov.argmax(1); bestfrac8 = (ov[np.arange(len(X)), best] * 8) // np.maximum(pop[best], 1)
        for T in (4, 5, 6, 7):
            pred = base.argmax(1).copy(); use = bestfrac8 > T; pred[use] = Ey[best[use]]
            rows.setdefault(f"gate{T}", []).append(split(pred))
    res[k] = {n: {key: round(float(np.mean([r[key] for r in v])), 4) for key in ("old", "new", "all")} for n, v in rows.items()}
    print(DS, "k", k, flush=True)
    for n, v in res[k].items():
        print(f"   {n:16s} old {v['old']:.3f} new {v['new']:.3f} all {v['all']:.3f}", flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", "results": res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"fewshot_fixes2_{DS}.json"), "w"), indent=1)
