"""Few-shot fix, round 4 (clothing and sound: the imprint swamps old classes whose codes share many bits):
  imprint        : IMPRINT as in the chip (CortexInt imprint=4), prototype x4 while n <= 8
  distinct       : imprint only on bits that every old class has on in under 1/4 of its examples
  +sleep S       : after the imprint, a short night of S dreams per known class (no self-stop): old classes' dreams
                   push the new rows back on the bits where they wrongly win (consolidation, existing hardware)
Setting as before: classes 0-4 known (all examples), 5-9 from k examples. 3 seeds, k = 1, 2, 5. Exact integer model.
usage: DATA_DIR DS"""
import json, os, sys, copy
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt, _dream, _practise
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y, te = f["y"], f["te"]; ytr, yte = y[~te], y[te]
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS)
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
old_te, new_te = yte < 5, yte >= 5; NEW = range(5, 10)
RULE = dict(B=10, night=2, daydream=1, night_stop=2)


def split(m):
    p = m.predict(cte) == yte
    return {"old": float(p[old_te].mean()), "new": float(p[new_te].mean()), "all": float(p.mean())}


def imprint(m, distinct):
    common = (m.on[:5].astype(np.int64) * 4 >= m.n[:5, None].astype(np.int64)).any(0)
    for c in NEW:
        n = int(m.n[c]); sh = n.bit_length() - 1
        up = np.minimum((m.on[c].astype(np.int32) * 4) >> sh, m.cmax)
        if distinct:
            up[common] = 0
        m.W[c] = np.maximum(m.W[c].astype(np.int32), up).astype(np.int8)


def sleep(m, S):
    buf = np.zeros(m.W.shape[1], np.int32); kn = np.where(m.known)[0]
    for j in range(S * len(kn)):
        c = kn[j % len(kn)]; k = _dream(m.on, m.n, c, m.rng, buf); _practise(m.W, buf, k, c, m.known, m.margin, m.cmax)


res = {}
for k in (1, 2, 5):
    rows = {}
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s)
        so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
        sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in NEW]); sn = sn[g.permutation(len(sn))]
        m0 = CortexInt(ctr.shape[1], seed=s, **RULE); m0.stage(ctr[so], ytr[so]); m0.stage(ctr[sn], ytr[sn])
        rows.setdefault("base", []).append(split(m0))
        for dist in (0, 1):
            for S in (0, 300, 1500):
                m = copy.deepcopy(m0); imprint(m, dist)
                if S:
                    sleep(m, S)
                rows.setdefault(("distinct" if dist else "imprint") + (f"+sleep{S}" if S else ""), []).append(split(m))
    res[k] = {n: {key: round(float(np.mean([r[key] for r in v])), 4) for key in ("old", "new", "all")} for n, v in rows.items()}
    print(DS, "k", k, flush=True)
    for n, v in res[k].items():
        print(f"   {n:18s} old {v['old']:.3f} new {v['new']:.3f} all {v['all']:.3f}", flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", "results": res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"fewshot_fixes4_{DS}.json"), "w"), indent=1)
