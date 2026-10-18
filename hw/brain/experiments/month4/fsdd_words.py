"""More words (20 Oct 2026): does learning the sound detectors from MANY more words help few-shot learning of new words? Extra words: the Free Spoken Digit Dataset (10 digits,
3,000 clips, 6 speakers; fsdd_prep.py), used UNLABELLED for detector fitting and, in scenario M, as extra KNOWN words. Speech Commands words 0-4 are known, 5-9 are learned from k recordings
(IMPRINT + short sleep, aligned pictures lead 6, 10 channels x 64 detectors). Detector sets: base (fit on words 0-1, as shipped) | more (FSDD all + Speech Commands words 0-4 sample) | fsdd (FSDD only: the
detectors have never heard any of the ten words). Scenarios: S (shipped: old = SC 0-4) and M (old = SC 0-4 + the 10 FSDD digits as 10 more known classes). 3 draws, single view: accuracy on all ten SC words /
new words / old words (SC test clips; M predicts over 20 classes). SIMULATED. usage: DATA_DIR"""
import os, sys, copy
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from feature_layer import Features
from cortex_int import CortexInt
from sound_align_confirm import align
D = sys.argv[1]
f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int)
fs = np.load(os.path.join(D, "fsdd_framesums_int.npz")); yfs = fs["y"].astype(int) + 10
P = align(S, 6); xtr, xte = P[~te], P[te]; xfs = align(fs["S"], 6)
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)); g0 = np.random.RandomState(5)
sets = {"base": xtr[np.isin(ytr, (0, 1))][:12000],
        "more": np.concatenate([xfs, xtr[np.isin(ytr, (0, 1, 2, 3, 4))][g0.permutation(int(np.isin(ytr, (0, 1, 2, 3, 4)).sum()))[:9000]]]),
        "fsdd": xfs}
for name, fit in sets.items():
    fes = [Features(64, thr=c).fit(fit) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([q.encode(x[i:i + 2000]) for q in fes], 1) for i in range(0, len(x), 2000)])
    ctr, cte, cfs = enc(xtr), enc(xte), enc(xfs)
    for scen in ("S", "M") if name == "more" else ("S",):
        for k in (1, 5):
            rows = []
            for s in (1, 2, 3):
                g = np.random.RandomState(1000 * s); so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
                sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
                m = CortexInt(ctr.shape[1], n_cls=20, seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2)
                if scen == "M":
                    A = np.concatenate([ctr[so], cfs]); Y = np.concatenate([ytr[so], yfs]); pp = g.permutation(len(Y)); m.stage(A[pp], Y[pp])
                else:
                    m.stage(ctr[so], ytr[so])
                m.stage(ctr[sn], ytr[sn])
                p = (cte.astype(np.int32) @ m.W.T.astype(np.int32)).argmax(1); nw = yte >= 5
                rows.append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean(), (p[nw] < 5).mean() + (p[nw] >= 10).mean()))
            a = np.mean(rows, 0); print(f"detectors {name:5s} scenario {scen} k={k}: all-10 {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}  new->old-or-FSDD {a[3]:.3f}", flush=True)
