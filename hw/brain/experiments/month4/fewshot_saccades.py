"""Few-shot with episodic recall: (a) saccades - each stored example is also stored shifted by one pooled cell in each
direction (the eye sees the object at slightly different places); (b) class score = sum of the top-m overlaps.
Spread codes r=1 (as in month 3), 3 seeds, 1 / 5 / 20 examples per class. Integer overlaps only. usage: DATA_DIR DS"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, DS); ytr = ytr.astype(int); yte = yte.astype(int)


def spread(code, r=1):
    m = code.reshape(len(code), 4, 6, 6, 32); out = np.zeros_like(m); p = np.pad(m, ((0, 0), (0, 0), (r, r), (r, r), (0, 0)))
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1):
            out |= p[:, :, dy:dy + 6, dx:dx + 6, :]
    return out.reshape(len(code), -1)


def shift(code, dy, dx):
    m = code.reshape(len(code), 4, 6, 6, 32); out = np.zeros_like(m)
    ys, yd = (slice(0, 6 - dy), slice(dy, 6)) if dy >= 0 else (slice(-dy, 6), slice(0, 6 + dy))
    xs, xd = (slice(0, 6 - dx), slice(dx, 6)) if dx >= 0 else (slice(-dx, 6), slice(0, 6 + dx))
    out[:, :, yd, xd] = m[:, :, ys, xs]
    return out.reshape(len(code), -1)


te = spread(cte).astype(np.int32)
for k in (1, 5, 20):
    res = {}
    for s in range(3):
        g = np.random.RandomState(s)
        idx = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(10)])
        base = ctr[idx]; Y = ytr[idx]
        for sacc in (0, 1):
            if sacc:
                X = np.concatenate([base] + [shift(base, dy, dx) for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0))])
                YY = np.tile(Y, 5)
            else:
                X, YY = base, Y
            Xs = spread(X).astype(np.int32)
            ov = te @ Xs.T - Xs.sum(1)[None] // 2
            for mtop in (1, 2, 3):
                sc = np.stack([np.sort(ov[:, YY == c], 1)[:, -min(mtop, (YY == c).sum()):].sum(1) for c in range(10)], 1)
                res.setdefault(f"sacc{sacc}_top{mtop}", []).append((sc.argmax(1) == yte).mean())
    print(DS, "k", k, {n: round(float(np.mean(v)), 3) for n, v in res.items()}, flush=True)
