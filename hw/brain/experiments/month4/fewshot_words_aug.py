"""New spoken words from a few recordings, with virtual examples: every new recording is also presented with its word
start moved to neighbouring frames (cochlea_int.align_word with lead 5 / 7, or 4..8): same recording, small time shifts
(integer address offset, no new hardware beyond word alignment). The chip knows words 0-4 (all examples, aligned at 6),
then learns words 5-9 from k recordings (k = 1, 2, 5) x the shifted copies (IMPRINT + short sleep, margin 32). Test:
single view (start 6) and LOOK AGAIN (starts 5, 6, 6, 7). 3 seeds. Exact integer chip model. usage: DATA_DIR"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea_int
from feature_layer import Features
from cortex_int import CortexInt
D = sys.argv[1]
f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]
ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
P0 = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8)
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
fes = [Features(64, thr=c).fit(cochlea_int.align_word(P0[~te], 6)[np.isin(ytr, (0, 1))][:12000]) for c in CH]
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 4000]) for g in fes], 1) for i in range(0, len(x), 4000)])
NEWi = np.where(ytr >= 5)[0]
codes = {L: None for L in (4, 5, 6, 7, 8)}
Ptr, Pte = P0[~te], P0[te]
c6 = enc(cochlea_int.align_word(Ptr, 6)); views_te = {L: enc(cochlea_int.align_word(Pte, L)).astype(np.int32) for L in (5, 6, 7)}
old_te, new_te = yte < 5, yte >= 5
SETS = {"none": [6], "5,6,7": [6, 5, 7], "4..8": [6, 4, 5, 7, 8]}
rows = {}
for k in (1, 2, 5):
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s)
        so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
        sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)])
        enc_cache = {L: enc(cochlea_int.align_word(Ptr[sn], L)) for L in (4, 5, 7, 8)}; enc_cache[6] = c6[sn]
        m0 = CortexInt(c6.shape[1], seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2)
        m0.stage(c6[so], ytr[so]); import copy
        for name, Ls in SETS.items():
            m = copy.deepcopy(m0)
            X = np.concatenate([enc_cache[L] for L in Ls]); Y = np.concatenate([ytr[sn]] * len(Ls))
            order = np.random.RandomState(s).permutation(len(X)); m.stage(X[order], Y[order])
            W = m.W.T.astype(np.int32)
            for vname, vs in (("single", [6]), ("look_again", [5, 6, 6, 7])):
                sc = sum(views_te[L] @ W for L in vs); p = sc.argmax(1) == yte
                rows.setdefault((k, name, vname), []).append({"old": float(p[old_te].mean()), "new": float(p[new_te].mean()), "all": float(p.mean())})
    for name in SETS:
        for vname in ("single", "look_again"):
            r = rows[(k, name, vname)]; print(f"k {k} {name:6s} {vname:10s}", {q: round(float(np.mean([t[q] for t in r])), 3) for q in ("old", "new", "all")}, flush=True)
json.dump({f"{k}|{n}|{vn}": {q: round(float(np.mean([t[q] for t in r])), 4) for q in ("old", "new", "all")} for (k, n, vn), r in rows.items()},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fewshot_words_aug.json"), "w"), indent=1)
