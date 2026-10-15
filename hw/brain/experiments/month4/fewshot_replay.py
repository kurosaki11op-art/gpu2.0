"""Few-shot with replay (hippocampus -> cortex): the table practises the k real examples per class plus dreams drawn
from those examples' dream counters (rejection-sampled like the chip), several passes. Spread codes (r=1) as month 3,
and plain codes; 3 seeds; k = 1, 5, 20. Compared with episodic recall (top-2). usage: DATA_DIR DS"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from sleep import SurpriseTable
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, DS); ytr = ytr.astype(int); yte = yte.astype(int); allk = np.ones(10, bool)


def spread(code, r=1):
    m = code.reshape(len(code), 4, 6, 6, 32); out = np.zeros_like(m); p = np.pad(m, ((0, 0), (0, 0), (r, r), (r, r), (0, 0)))
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            out |= p[:, :, dy:dy + 6, dx:dx + 6, :]
    return out.reshape(len(code), -1)


for sp in (0, 1):
    te = spread(cte) if sp else cte
    for k in (1, 5, 20):
        res = {}
        for s in range(3):
            g = np.random.RandomState(s)
            idx = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(10)])
            X = spread(ctr[idx]) if sp else ctr[idx]; Y = ytr[idx]
            for nd in (0, 50, 200):
                Xs, Ys = [X], [Y]
                if nd:
                    for c in range(10):
                        p = X[Y == c].mean(0); Xs.append(g.random_sample((nd, X.shape[1])) < p); Ys.append(np.full(nd, c))
                XX, YY = np.concatenate(Xs), np.concatenate(Ys)
                st = SurpriseTable(X.shape[1], 10, cmax=15).practise(XX, YY, allk, epochs=10, seed=s)
                res.setdefault(f"dreams{nd}", []).append((st.predict(te, allk) == yte).mean())
            ov = te.astype(np.int32) @ X.astype(np.int32).T - X.sum(1)[None] // 2
            sc = np.stack([np.sort(ov[:, Y == c], 1)[:, -min(2, k):].sum(1) for c in range(10)], 1)
            res.setdefault("episodic_top2", []).append((sc.argmax(1) == yte).mean())
        print(DS, "spread", sp, "k", k, {n: round(float(np.mean(v)), 3) for n, v in res.items()}, flush=True)
