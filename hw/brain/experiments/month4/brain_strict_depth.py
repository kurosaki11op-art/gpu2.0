"""Does depth raise the ceiling? (20 Oct 2026) DIAGNOSTIC, SIMULATED. Layer 2 = competitive Hebbian detectors (agreement count, no multiplies) over 3x3 neighbourhoods of the layer-1 map (all four channels stacked), learned on the first stage's images only; code = winner per spot
(k winners), OR-pooled none. Float dual-ridge readout as a ceiling probe on layer 2 alone and on layer 1 + layer 2. usage: DATA_DIR; env DS, NPS."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import detector_learn
from cortex_core import load
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); NPS = int(os.environ.get("NPS", 2000)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]; Y = np.eye(10, dtype=np.float32)[ytr]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
c1tr, c1te = enc(xtr), enc(xte); F1 = fes[0].F; m = int(round((c1tr.shape[1] // (len(fes) * F1)) ** 0.5)); print("layer 1", c1tr.shape, "map", m, "x", m, flush=True)


def maps(c):                                                   # (B, m, m, channels*F1)
    B = len(c); return np.concatenate([c[:, i * m * m * F1:(i + 1) * m * m * F1].reshape(B, m, m, F1) for i in range(len(fes))], 3)


def nbh(mp, s):                                                # all s x s neighbourhoods -> (B, n, n, s*s*C) bool
    B, h, w, C = mp.shape; n = h - s + 1
    return np.concatenate([mp[:, i:i + n, j:j + n, :] for i in range(s) for j in range(s)], 3), n


def fit2(p, F, passes=4, cmax=31, seed=0):
    r = np.random.RandomState(seed); p = p[p.sum(1) >= 3]; cnt = np.where(p[r.choice(len(p), F)], 1, -1).astype(np.int32)
    for _ in range(passes):
        wins = np.zeros(F, int)
        for i in range(0, len(p), 2000):
            b = p[i:i + 2000]; w = (np.where(b, 1, -1).astype(np.int16) @ np.where(cnt >= 0, 1, -1).astype(np.int16).T).argmax(1)
            np.add.at(cnt, w, np.where(b, 1, -1)); np.clip(cnt, -cmax, cmax, out=cnt); wins += np.bincount(w, minlength=F)
        dead = np.where(wins == 0)[0]; cnt[dead] = np.where(p[r.choice(len(p), len(dead))], 1, -1)
    return cnt


def enc2(mp, cnt, s, k):
    v, n = nbh(mp, s); B = len(mp); flat = v.reshape(-1, v.shape[-1]); t = np.where(cnt >= 0, 1, -1).astype(np.int16); out = np.zeros((len(flat), len(cnt)), bool)
    for i in range(0, len(flat), 20000):
        b = flat[i:i + 20000]; sc = np.where(b, 1, -1).astype(np.int16) @ t.T; w = np.argsort(-sc, 1)[:, :k]; ok = b.sum(1) >= 3
        for kk in range(k): out[np.arange(i, i + len(b))[ok], w[ok, kk]] = True
    return out.reshape(B, -1)


def ridge(ctr, cte):
    ctr = ctr.astype(np.float32); cte = cte.astype(np.float32); mu = ctr.mean(0); A = ctr - mu; Kt = A @ A.T; Kte = (cte - mu) @ A.T; best = 0
    for lam in (30.0, 100.0, 300.0, 1000.0, 3000.0):
        al = np.linalg.solve(Kt + lam * np.eye(len(Kt), dtype=np.float32), Y - Y.mean(0)); best = max(best, float(((Kte @ al).argmax(1) == yte).mean()))
    return best


print(DS, "layer 1 alone", round(ridge(c1tr, c1te), 4), flush=True)
mtr, mte = maps(c1tr), maps(c1te); first = np.isin(ytr, STAGES[0])
for s, F2, k in ((3, 64, 1), (3, 128, 1), (3, 128, 3), (2, 128, 3)):
    p, _ = nbh(mtr[first], s); cnt = fit2(p.reshape(-1, p.shape[-1]), F2); a, b = enc2(mtr, cnt, s, k), enc2(mte, cnt, s, k)
    print(DS, "layer 2 s=%d F2=%d k=%d" % (s, F2, k), a.shape[1], "bits: alone", round(ridge(a, b), 4), " layer1+2", round(ridge(np.concatenate([c1tr, a], 1), np.concatenate([c1te, b], 1)), 4), flush=True)
