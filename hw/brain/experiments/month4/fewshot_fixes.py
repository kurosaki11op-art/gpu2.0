"""Fixes for "a new class from a few examples is outvoted after shipping" (research note:
docs/research/fewshot_class_incremental.md). The chip learns classes 0-4 from all their examples (one stage), then
5-9 from k examples each (second stage, month-2 rule). Then, on the same trained chip, variants of the readout / write:
  base        : table only (today)
  imprint W0  : one-shot imprint (C-FSCIL mode 1 / weight imprinting / novelty gating): each new example adds
                step = W0 >> floor(log2 n) (n = its index in the class, at least 1) on its active bits (clipped at 15)
  align       : per-class norm alignment (Weight Aligning, integer form): class score << s_c, s_c = floor(log2(Nmax/N_c))
                with N_c = sum |W_c| (capped at 4)
  hippo <<s   : hippocampus gating (complementary learning systems): new classes also score their best stored episode,
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
        base = scores(m.W, m.known)
        rows.setdefault("base", []).append(split(base.argmax(1)))
        rows.setdefault("align", []).append(split(align(base, m.W).argmax(1)))
        for W0 in (4, 8, 15):
            W = m.W.astype(np.int16).copy(); cnt = np.zeros(10, np.int64)
            for i in sn:
                c = ytr[i]; cnt[c] += 1; step = max(1, W0 >> int(np.floor(np.log2(cnt[c]))))
                a = np.nonzero(ctr[i])[0]; W[c, a] = np.minimum(W[c, a] + step, 15)
            si = scores(W, m.known)
            rows.setdefault(f"imprint{W0}", []).append(split(si.argmax(1)))
            rows.setdefault(f"imprint{W0}+align", []).append(split(align(si, W).argmax(1)))
        E = ctr[sn].astype(np.int32); Ey = ytr[sn]
        ov = X @ E.T - E.sum(1)[None] // 2
        ep = np.full((len(X), 10), 0, np.int64)
        for c in NEW:
            ep[:, c] = ov[:, Ey == c].max(1)
        for sh in (0, 1, 2, 3):
            rows.setdefault(f"hippo<<{sh}", []).append(split((base + (ep << sh)).argmax(1)))
    res[k] = {n: {key: round(float(np.mean([r[key] for r in v])), 4) for key in ("old", "new", "all")} for n, v in rows.items()}
    print(DS, "k", k, flush=True)
    for n, v in res[k].items():
        print(f"   {n:16s} old {v['old']:.3f} new {v['new']:.3f} all {v['all']:.3f}", flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", "results": res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"fewshot_fixes_{DS}.json"), "w"), indent=1)
