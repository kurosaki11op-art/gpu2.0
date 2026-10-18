"""Self-training (unlabelled refinement) for new spoken words (19-20 Oct): chip knows words 0-4, learns 5-9 from k labelled recordings (IMPRINT + short sleep, aligned codes), then hears an
UNLABELLED pool (NU clips per word of all ten words, none of the labelled ones, none of the test clips). Round r: score the pool with the current table; a clip is assigned the predicted class and
learned (count + practise, the usual stage rule) when (a) the prediction is a NEW class (5-9) and (b) its margin (top - second score) > TAU; rounds R. Brain analogue: ongoing Hebbian
refinement on the stream. Compared at the end on the test clips: all ten words / new words / old words, and the precision of the pseudo-labels. 3 draws, single view. SIMULATED. usage: DATA_DIR NU R TAU [TAU ...]"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
D, NU, R = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); TAUS = [int(v) for v in sys.argv[4:]]
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int); ctr, cte = z["tr"], z["te"].astype(np.int32)
for k in [int(v) for v in os.environ.get("KS", "1,2,5").split(",")]:
    rows = {}
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s); so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
        oldpool = np.concatenate([g.choice(np.where(ytr == c)[0], NU, replace=False) for c in range(5)]); so = np.setdiff1d(so, oldpool); so = so[g.permutation(len(so))]
        sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
        rest = np.setdiff1d(np.where(ytr >= 5)[0], sn)
        pool = np.concatenate([oldpool] + [g.choice(rest[ytr[rest] == c], NU, replace=False) for c in range(5, 10)]); pool = pool[g.permutation(len(pool))]
        m0 = CortexInt(ctr.shape[1], seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2); m0.stage(ctr[so], ytr[so]); m0.stage(ctr[sn], ytr[sn])
        import copy
        for tau in [None] + TAUS:
            m = copy.deepcopy(m0); prec = []
            if tau is not None:
                for r in range(R):
                    sc = ctr[pool].astype(np.int32) @ m.W.T.astype(np.int32); part = np.sort(sc, 1); marg = part[:, -1] - part[:, -2]; pred = sc.argmax(1)
                    sel = np.where((pred >= 5) & (marg > tau))[0]
                    if len(sel) == 0: break
                    prec.append(float((pred[sel] == ytr[pool][sel]).mean()))
                    m.stage(ctr[pool][sel], pred[sel])
            p = (cte @ m.W.T.astype(np.int32)).argmax(1); nw = yte >= 5
            rows.setdefault(tau, []).append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean(), float(np.mean(prec)) if prec else float("nan")))
    for tau, v in rows.items():
        a = np.nanmean(v, 0); print(f"k={k} tau={tau}: all-10 {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}  pseudo-label precision {a[3]:.2f}", flush=True)
