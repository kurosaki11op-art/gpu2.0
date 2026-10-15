"""Few-shot: rarity-weighted recall. Each code bit gets a small integer weight from how often it fires on unlabeled
images (a free-running counter per bit; weight = how many halvings it is below the most common bit, capped). A rare
bit shared with a stored example counts more than a common one (surprise carries information). Score = weighted
overlap minus half the stored example's weighted size; adds of small integers only, no multiplies on chip (a weight
of 1..4 is added, not multiplied). Episodic recall on spread codes as in fewshot_saccades.py, 3 seeds, top-1/top-2.
usage: DATA_DIR DS"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from fewshot_saccades_lib import spread
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, DS); ytr = ytr.astype(int); yte = yte.astype(int)
te = spread(cte).astype(np.int32)
cnt = spread(ctr[np.random.RandomState(9).choice(len(ctr), 10000, replace=False)]).sum(0).astype(np.int64) + 1
L = np.floor(np.log2(cnt.max() / cnt)).astype(np.int64)
W = {"plain": np.ones_like(L), "w1to4": 1 + np.clip(L, 0, 3), "w0to3": np.clip(L, 0, 3), "w1to8": 1 + np.clip(L, 0, 7)}
res = {}
for k in (1, 5, 20):
    r = {}
    for s in range(3):
        g = np.random.RandomState(s)
        idx = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(10)])
        Xs = spread(ctr[idx]).astype(np.int32); YY = ytr[idx]
        for wn, w in W.items():
            ov = (te * w) @ Xs.T - (Xs * w).sum(1)[None] // 2
            for mtop in (1, 2):
                sc = np.stack([np.sort(ov[:, YY == c], 1)[:, -min(mtop, k):].sum(1) for c in range(10)], 1)
                r.setdefault(f"{wn}_top{mtop}", []).append(float((sc.argmax(1) == yte).mean()))
    res[k] = {n: round(float(np.mean(v)), 4) for n, v in r.items()}
    print(DS, "k", k, res[k], flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (episodic recall, spread codes, 3 seeds)", "results": res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"fewshot_rarity_{DS}.json"), "w"), indent=1)
