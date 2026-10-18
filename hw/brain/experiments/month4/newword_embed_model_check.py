"""Accuracy of the hardware-exact embedding rules (cortex_embed.CortexEmbed): table trained on SC words 0-4 + FSDD digits (16 table rows, 15 known), old words with KOLD prototypes by integer competitive learning (sh = 5,
slots K per class, winner / empty-first), new words 5-9 from k recordings (sh = 0 running mean). k = 1, 2, 5, KOLD = 1, 3, 4; 3 draws, single view; all ten / new / old. usage: DATA_DIR. SIMULATED."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_embed import CortexEmbed
D = sys.argv[1]
c = np.load(os.path.join(D, os.environ.get("CODES", "word_codes_shipped.npz"))); ctr, cte, cfs, yfs = c["tr"], c["te"], c["fs"], c["yfs"].astype(int) + 6
f = np.load(os.path.join(D, "speech_framesums_int.npz")); y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int)
# table rows: SC old words 0-4 -> rows 0-4; FSDD digits -> rows 6-15 (row 5 unused; new words never get rows)
old = np.where(ytr < 5)[0]; g0 = np.random.RandomState(0)
m0 = CortexEmbed(ctr.shape[1], n_cls=16, np_slots=48, seed=1, night=0, daydream=0)
A = np.concatenate([ctr[old], cfs]); Y = np.concatenate([ytr[old], yfs]); pp = g0.permutation(len(Y)); m0.stage(A[pp], Y[pp])
Etr = m0.embedding_batch(ctr); Ete = m0.embedding_batch(cte)
for KOLD in (1, 3, 4):
    for k in (1, 2, 5):
        rows = []
        for s in (1, 2, 3):
            m = CortexEmbed(ctr.shape[1], n_cls=16, np_slots=48, seed=1); m.W = m0.W; m.known = m0.known
            for cl in range(5):                                              # old words: competitive learning over their training clips (shuffled), slots cl*KOLD ..
                idx = np.where(ytr == cl)[0]; idx = idx[np.random.RandomState(s * 10 + cl).permutation(len(idx))]
                for i in idx:
                    sl = m.winner(Etr[i], cl * KOLD, KOLD); m.enroll(Etr[i], sl, cl, sh=5)
            g = np.random.RandomState(1000 * s)
            for cl in range(5, 10):
                for i in g.choice(np.where(ytr == cl)[0], k, replace=False):
                    m.enroll(Etr[i], 20 + cl - 5, cl, sh=0)
            p = m.match_batch(Ete); nw = yte >= 5
            rows.append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
        a = np.mean(rows, 0); print(f"hardware-exact rules KOLD={KOLD} k={k}: all-10 {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}", flush=True)
