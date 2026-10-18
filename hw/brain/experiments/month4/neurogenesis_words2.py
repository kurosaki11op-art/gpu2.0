"""Neurogenesis for new spoken words (19 Oct): the chip knows words 0-4 (codes from the shipped detectors, F = 64 per channel, fitted on words 0-1). When it learns
new words 5-9 from k recordings each, it GROWS FNEW extra detectors per channel, fitted without labels on the windows of those few new recordings only; old rows and old
codes are untouched (the old words were learned before the new bits existed: those bits are 0 for them). New bits are appended to the code of the new recordings and of all test clips.
Compared with no growth (same k). IMPRINT + short sleep for the new words, aligned pictures (lead 6), 10 channels. Accuracy 10-way, new words 10-way, new words 5-way. 3 draws.
SIMULATED. Variant: env REPLAY=m keeps m stored old recordings per old word (a small episodic buffer, NOT the usual no-stored-examples rule) and teaches the old rows the new bits from them before the new words are learned. usage: DATA_DIR FNEW"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from feature_layer import Features
from cortex_int import CortexInt
from sound_align_confirm import align
D, FNEW = sys.argv[1], int(sys.argv[2]); REPLAY = int(os.environ.get("REPLAY", "0"))
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
S, y, te = f["S"], f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int); ctr, cte = z["tr"], z["te"]
P = align(S, 6); xtr, xte = P[~te], P[te]
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
NB = ctr.shape[1]
for k in (1, 2, 5):
    res = {"base": [], "grow": []}
    for s in (1, 2):
        g = np.random.RandomState(1000 * s); so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
        sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
        fes = [Features(FNEW, thr=c, seed=s).fit(xtr[sn], n_patches=100000, passes=3) for c in CH]
        enc = lambda x: np.concatenate([np.concatenate([q.encode(x[i:i + 2000]) for q in fes], 1) for i in range(0, len(x), 2000)])
        newtr, newte = enc(xtr[sn]), enc(xte)
        ex = np.concatenate([g.choice(np.where(ytr == c)[0], REPLAY, replace=False) for c in range(5)]) if REPLAY else None
        exfull = np.concatenate([ctr[ex], enc(xtr[ex])], 1) if REPLAY else None
        for name in (("grow",) if REPLAY else ("base", "grow")):
            nb = NB + (newtr.shape[1] if name == "grow" else 0)
            m = CortexInt(nb, seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2)
            A = np.concatenate([ctr[so], np.zeros((len(so), nb - NB), bool)], 1) if name == "grow" else ctr[so]
            m.stage(A, ytr[so])
            if name == "grow" and REPLAY:
                pp = g.permutation(len(ex)); m.stage(exfull[pp], ytr[ex][pp])
            B_ = np.concatenate([ctr[sn], newtr], 1) if name == "grow" else ctr[sn]
            m.stage(B_, ytr[sn])
            T = np.concatenate([cte, newte], 1) if name == "grow" else cte
            sc = T.astype(np.int32) @ m.W.T.astype(np.int32); p = sc.argmax(1); nw = yte >= 5
            res[name].append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (sc[nw][:, 5:].argmax(1) + 5 == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
    for name, v in res.items():
        a = np.mean(v, 0); print(f"REPLAY={REPLAY} k={k} {name:5s}: all-10 {a[0]:.3f}  new(10-way) {a[1]:.3f}  new(5-way) {a[2]:.3f}  old {a[3]:.3f}", flush=True)
