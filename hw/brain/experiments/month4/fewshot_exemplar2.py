"""Exemplar memory vs table imprint for new words, same codes (aligned, detectors fitted on words 0-1), IMPRINT + short sleep model:
5-way among new words (table scores restricted to classes 5-9) vs exemplar nearest neighbour, and a 10-way fusion: a clip goes to a
new word when its best exemplar overlap (cosine-like, integer-friendly) exceeds THR times its overlap with the best old-class mean,
else the table decides among old words. 5 draws. SIMULATED. usage: DATA_DIR"""
import os, sys, json, copy
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
D = sys.argv[1]
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int)
ctr, cte = z["tr"], z["te"]; cf, tf = ctr.astype(np.float32), cte.astype(np.float32)
rows = {}
for k in (1, 2, 5):
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s)
        so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
        sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)])
        m = CortexInt(ctr.shape[1], seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2)
        m.stage(ctr[so], ytr[so]); m.stage(ctr[sn][np.random.RandomState(s).permutation(len(sn))], ytr[sn][np.random.RandomState(s).permutation(len(sn))]) if False else None
        order = np.random.RandomState(s).permutation(len(sn)); m.stage(ctr[sn][order], ytr[sn][order])
        W = m.W.T.astype(np.int32); sc = cte.astype(np.int32) @ W
        new = yte >= 5
        t5 = (sc[new][:, 5:].argmax(1) + 5 == yte[new]).mean()
        E, Ey = cf[sn], ytr[sn]; T = tf
        inter = T @ E.T; cos = inter / np.sqrt((T.sum(1)[:, None] + 1) * (E.sum(1)[None, :] + 1))
        best = np.stack([cos[:, Ey == c].max(1) for c in range(5, 10)], 1)
        e5 = (best[new].argmax(1) + 5 == yte[new]).mean()
        # old-class prototype overlap (mean code of each old word, same cosine)
        P = np.stack([cf[ytr == c].mean(0) for c in range(5)]); pc = (T @ P.T) / np.sqrt((T.sum(1)[:, None] + 1) * ((P * P).sum(1)[None, :] + 1e-3))
        r = {"table5": float(t5), "exemplar5": float(e5), "table10": float((sc.argmax(1) == yte).mean())}
        for thr in (0.7, 0.8, 0.9, 1.0, 1.1):
            newscore = best.max(1); oldscore = pc.max(1) * 0 + (np.sqrt(((T * T).sum(1))) * 0)
            use_new = best.max(1) > thr * pc.max(1)
            pred = np.where(use_new, best.argmax(1) + 5, sc[:, :5].argmax(1))
            r[f"fuse{thr}"] = float((pred == yte).mean())
        for kk, v in r.items(): rows.setdefault((k, kk), []).append(v)
    print(k, {kk: round(float(np.mean(v)), 3) for (kq, kk), v in rows.items() if kq == k}, flush=True)
json.dump({f"{k}|{kk}": round(float(np.mean(v)), 4) for (k, kk), v in rows.items()}, open("fewshot_exemplar2.json", "w"), indent=1)
