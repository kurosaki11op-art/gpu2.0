"""Candidates B and D from the 20 Oct review prompts, on our codes (sparse 23,040-bit aligned word codes, per-class on-counters = occurrence counts, no stored exemplars):
  B (pair-specific discriminative counters): when the table's top two classes are one NEW and one OLD class (n, o), count votes over the clip's ACTIVE bits: w = +1 if the bit is reliably present in n
     (rate >= TH) and rare in o (rate <= TL); w = -1 if reliably present in o and rare in n; v = sum w over active bits; choose n if v >= V, o if v <= -V, else keep the table's choice.
  D (reliable negative evidence): for the pair, the fraction of each class's reliably-present bits (rate >= TH) that are MISSING in the clip; the class with the smaller missing fraction wins when the difference > MARGIN (per mille).
V and MARGIN are chosen on a development set (training clips never used for enrolment, never test clips). Table = chip after IMPRINT + short sleep. 3 draws, single view, SIMULATED.
Reported: all ten / new / old accuracy, new->old and old->new error rates, vs the plain table. usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
D = sys.argv[1]
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int); ctr, cte = z["tr"], z["te"]
NEW = np.arange(5, 10)


def decide(codes, W, rates, nrate_cnt, mode, par):
    sc = codes.astype(np.int32) @ W.T.astype(np.int32); order = np.argsort(-sc, 1); a, b = order[:, 0], order[:, 1]; pred = a.copy()
    pair = (np.isin(a, NEW) != np.isin(b, NEW))
    TH, TL, V = par
    for i in np.where(pair)[0]:
        n, o = (a[i], b[i]) if a[i] >= 5 else (b[i], a[i]); act = codes[i].astype(bool)
        if mode == "B":
            wn = (rates[n] >= TH) & (rates[o] <= TL); wo = (rates[o] >= TH) & (rates[n] <= TL)
            v = int(wn[act].sum()) - int(wo[act].sum())
            if v >= V: pred[i] = n
            elif v <= -V: pred[i] = o
        else:
            pn = rates[n] >= TH; po = rates[o] >= TH
            mn = 1000 * (pn & ~act).sum() // max(pn.sum(), 1); mo = 1000 * (po & ~act).sum() // max(po.sum(), 1)
            if mo - mn > V: pred[i] = n
            elif mn - mo > V: pred[i] = o
    return pred


def stats(p, yv):
    nw = yv >= 5
    return ((p == yv).mean(), (p[nw] == yv[nw]).mean(), (p[~nw] == yv[~nw]).mean(), (p[nw] < 5).mean(), (p[~nw] >= 5).mean())


for k in (1, 5):
    rows = {}
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s)
        dev = np.concatenate([g.choice(np.where(ytr == c)[0], 60, replace=False) for c in range(10)])
        so = np.setdiff1d(np.where(ytr < 5)[0], dev); so = so[g.permutation(len(so))]
        avail = np.setdiff1d(np.where(ytr >= 5)[0], dev)
        sn = np.concatenate([g.choice(avail[ytr[avail] == c], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
        m = CortexInt(ctr.shape[1], seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2); m.stage(ctr[so], ytr[so]); m.stage(ctr[sn], ytr[sn])
        rates = (m.on.astype(np.float32) / np.maximum(m.n, 1)[:, None])
        # new classes: exact rates from their k recordings (the counters were halved only when full)
        rates_new = np.stack([ctr[sn][ytr[sn] == c].mean(0) for c in range(5, 10)]); rates[5:] = rates_new
        W = m.W
        plain = (cte.astype(np.int32) @ W.T.astype(np.int32)).argmax(1); rows.setdefault("plain", []).append(stats(plain, yte))
        for mode, grid in (("B", [(1.0 if k == 1 else 0.6, tl, v) for tl in (0.05, 0.25) for v in (1, 3, 8, 16)]), ("D", [(th, 0, v) for th in (0.5, 0.75) for v in (0, 50, 150)])):
            best, bp = -1, None
            for par in grid:
                pd = decide(ctr[dev], W, rates, None, mode, par); a = (pd == ytr[dev]).mean()
                if a > best: best, bp = a, par
            pt = decide(cte, W, rates, None, mode, bp); rows.setdefault(mode, []).append(stats(pt, yte))
            rows.setdefault(mode + "_par", []).append(bp)
    for name, v in rows.items():
        if name.endswith("_par"): print(f"k={k} {name}: {v}", flush=True); continue
        a = np.mean(v, 0); sd = np.std([x[0] for x in v])
        print(f"k={k} {name:6s}: all-10 {a[0]:.3f} (sd {sd:.3f})  new {a[1]:.3f}  old {a[2]:.3f}  new->old {a[3]:.3f}  old->new {a[4]:.3f}", flush=True)
