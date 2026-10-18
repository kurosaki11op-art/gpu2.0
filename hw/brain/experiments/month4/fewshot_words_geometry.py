"""Does a finer sound-code geometry help few-shot new words? (twin pairs such as no/go, left/right differ in short onsets; the shipped code pools 2 x 2 spots at stride 2.)
spec = ph,pw,sy,sx,py,px,F (sound_features.SoundFeatures). Detectors fitted on words 0-1 (as shipped), aligned pictures (lead 6). Protocol: chip knows words 0-4, learns 5-9 from k = 1, 5 recordings
(IMPRINT + short sleep), 3 draws, single view: all ten words / new words / old words. usage: DATA_DIR spec [...]. SIMULATED."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from sound_features import SoundFeatures
from cortex_int import CortexInt
from sound_align_confirm import align
D = sys.argv[1]
f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]
ytr, yte = y[~te].astype(int), y[te].astype(int); P = align(S, 6); xtr, xte = P[~te], P[te]
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
for spec in sys.argv[2:]:
    ph, pw, sy, sx, py, px, F = [int(v) for v in spec.split(",")]
    fes = [SoundFeatures(F, c, ph, pw, sy, sx, py, px).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([q.encode(x[i:i + 2000]) for q in fes], 1) for i in range(0, len(x), 2000)])
    ctr, cte = enc(xtr), enc(xte)
    for k in (1, 5):
        rows = []
        for s in (1, 2, 3):
            g = np.random.RandomState(1000 * s); so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
            sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
            m = CortexInt(ctr.shape[1], seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2); m.stage(ctr[so], ytr[so]); m.stage(ctr[sn], ytr[sn])
            p = (cte.astype(np.int32) @ m.W.T.astype(np.int32)).argmax(1); nw = yte >= 5
            rows.append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
        a = np.mean(rows, 0); print(f"{spec} bits {ctr.shape[1]} k={k}: all-10 {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}", flush=True)
