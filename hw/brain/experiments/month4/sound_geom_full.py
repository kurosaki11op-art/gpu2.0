"""Full check of a sound-code geometry before adopting it (20 Oct): spec = ph,pw,sy,sx,py,px,F (sound_features.SoundFeatures), slow table K = 5 (CH 100) as the chip option. Reports, 3 seeds, single view:
words all at once, words in 5 stages, and few-shot after shipping (k = 1, 2, 5: all ten words / new / old). Same detectors-fit rule as shipped (words 0-1), aligned pictures (lead 6). No change is adopted
unless EVERY number is at least as good as the shipped geometry 5,5,2,2,2,2,64. usage: DATA_DIR spec [...]. SIMULATED."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from sound_features import SoundFeatures
from cortex_slow import CortexSlow
from sound_align_confirm import align
D = sys.argv[1]
f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]
ytr, yte = y[~te].astype(int), y[te].astype(int); P = align(S, 6); xtr, xte = P[~te], P[te]
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
for spec in sys.argv[2:]:
    ph, pw, sy, sx, py, px, F = [int(v) for v in spec.split(",")]
    fes = [SoundFeatures(F, c, ph, pw, sy, sx, py, px).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([q.encode(x[i:i + 2000]) for q in fes], 1) for i in range(0, len(x), 2000)])
    ctr, cte = enc(xtr), enc(xte); nb = ctr.shape[1]
    mk = lambda s: CortexSlow(nb, ch=100, K=5, seed=s, night_stop=2, daydream=1)
    for sname, stages in (("all at once", [tuple(range(10))]), ("5 stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])):
        accs = []
        for s in (1, 2, 3):
            m = mk(s)
            for i, st in enumerate(stages):
                sel = np.where(np.isin(ytr, st))[0]; sel = sel[np.random.RandomState(100 * s + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
            accs.append(float((m.predict(cte) == yte).mean()))
        print(f"{spec} bits {nb} {sname}: {np.mean(accs):.4f}", flush=True)
    for k in (1, 2, 5):
        rows = []
        for s in (1, 2, 3):
            g = np.random.RandomState(1000 * s); so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
            sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
            m = CortexSlow(nb, ch=100, K=5, seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2); m.stage(ctr[so], ytr[so]); m.stage(ctr[sn], ytr[sn])
            p = m.predict(cte); nw = yte >= 5
            rows.append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
        a = np.mean(rows, 0); print(f"{spec} few-shot k={k}: all-10 {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}", flush=True)
