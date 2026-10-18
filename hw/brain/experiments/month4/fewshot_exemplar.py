"""Diagnostic for an episodic (hippocampus-like) exemplar memory for new words: keep the k stored sparse codes of each new word and
classify a test clip by the best overlap (popcount of AND, normalised by the stored code's on-bits... variants) against the stored
exemplars. 5-way among new words 5-9 (and 10-way with a prototype score for old words 0-4 using the class mean overlap). SIMULATED.
usage: DATA_DIR"""
import os, sys, json
import numpy as np
D = sys.argv[1]
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int)
ctr, cte = z["tr"].astype(np.float32), z["te"].astype(np.float32)
res = {}
for k in (1, 2, 5):
    for mode in ("and", "jaccard", "cos"):
        accs = []
        for s in (1, 2, 3, 4, 5):
            g = np.random.RandomState(1000 * s)
            idx = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)])
            E, Ey = ctr[idx], ytr[idx]
            m = yte >= 5; T = cte[m]; ty = yte[m]
            inter = T @ E.T
            if mode == "and": sc = inter
            elif mode == "jaccard": sc = inter / (T.sum(1)[:, None] + E.sum(1)[None, :] - inter + 1)
            else: sc = inter / np.sqrt((T.sum(1)[:, None] + 1) * (E.sum(1)[None, :] + 1))
            best = np.stack([sc[:, Ey == c].max(1) for c in range(5, 10)], 1)
            accs.append(float((best.argmax(1) + 5 == ty).mean()))
        res[f"k{k}_{mode}"] = round(float(np.mean(accs)), 4); print(k, mode, res[f"k{k}_{mode}"], flush=True)
json.dump({"label": "SIMULATED, 5-way among the new words 5-9, 5 draws", **res}, open("fewshot_exemplar.json", "w"), indent=1)
