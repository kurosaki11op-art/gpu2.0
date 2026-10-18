"""Where do new spoken words fail? Chip knows words 0-4, learns 5-9 from k recordings (IMPRINT + short sleep, aligned codes). For test clips of the new words:
share predicted correctly / as another NEW word / as an OLD word; and for old-word clips: share kept / lost to a new word / confused with another old word. 3 draws. SIMULATED."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
D = sys.argv[1]
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int); ctr, cte = z["tr"], z["te"]
for k in (1, 5):
    r = []
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s); so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
        sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
        m = CortexInt(ctr.shape[1], seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2); m.stage(ctr[so], ytr[so]); m.stage(ctr[sn], ytr[sn])
        p = m.predict(cte); nw = yte >= 5; ow = ~nw
        r.append([(p[nw] == yte[nw]).mean(), ((p[nw] >= 5) & (p[nw] != yte[nw])).mean(), (p[nw] < 5).mean(), (p[ow] == yte[ow]).mean(), ((p[ow] >= 5)).mean(), ((p[ow] < 5) & (p[ow] != yte[ow])).mean()])
    a = np.mean(r, 0)
    print(f"k={k}: NEW-word clips: correct {a[0]:.2f}, as another new word {a[1]:.2f}, as an OLD word {a[2]:.2f} | OLD-word clips: kept {a[3]:.2f}, lost to a new word {a[4]:.2f}, other old word {a[5]:.2f}")
