"""Hybrid for new words (20 Oct): the table (trained on the 5 old SC words + NK FSDD digits, NO rows for the new words) answers old words when it is confident; otherwise the table-score embedding decides.
Embedding = integer table scores over the known classes; prototypes = mean embedding (new words from k recordings, old words from their training clips, FSDD digits excluded from the 10-word decision);
distance = L1. Gate: the table's top-1 class is an old SC word (0-4) and its margin (top1 - top2 over the known classes) >= MARGIN; MARGIN is the smallest value for which, on a development set of old-word training clips
(never test clips, not used to train the table), the hybrid keeps the table's old-word accuracy within 1 point. 3 draws, single view, SIMULATED. usage: DATA_DIR NK"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
D, NK = sys.argv[1], int(sys.argv[2])
c = np.load(os.path.join(D, "word_codes_shipped.npz")); ctr, cte, cfs, yfs = c["tr"], c["te"], c["fs"], c["yfs"].astype(int) + 10
f = np.load(os.path.join(D, "speech_framesums_int.npz")); y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int)
digits = list(range(10, 10 + NK)); sel = np.isin(yfs, digits); g0 = np.random.RandomState(0)
dev = np.concatenate([g0.choice(np.where(ytr == cl)[0], 100, replace=False) for cl in range(5)]); old = np.setdiff1d(np.where(ytr < 5)[0], dev)
m = CortexInt(ctr.shape[1], n_cls=20, seed=1, night=0, daydream=0)
A = np.concatenate([ctr[old], cfs[sel]]); Y = np.concatenate([ytr[old], yfs[sel]]); pp = g0.permutation(len(Y)); m.stage(A[pp], Y[pp])
keep = list(range(5)) + digits; W = m.W[keep].astype(np.int32)
z = lambda X: (X.astype(np.int32) @ W.T)
ztr, zte, zdev = z(ctr), z(cte), z(ctr[dev])
order = lambda s: np.sort(s, 1)


def table_pred(s): return s.argmax(1)


def margin(s): o = order(s); return o[:, -1] - o[:, -2]


for k in (1, 5):
    rows = {"table(no new rows)": [], "embedding": [], "hybrid": []}
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s); idx = {cl: g.choice(np.where(ytr == cl)[0], k, replace=False) for cl in range(5, 10)}
        zf = ztr.astype(np.float32); proto = np.stack([zf[np.setdiff1d(np.where(ytr == cl)[0], dev)].mean(0) for cl in range(5)] + [zf[idx[cl]].mean(0) for cl in range(5, 10)])
        emb = lambda zz: (-np.abs(zz.astype(np.float32)[:, None, :] - proto[None]).sum(2)).argmax(1)
        pe_dev = emb(zdev); pt_dev = table_pred(zdev); tp_dev = np.where(pt_dev < 5, pt_dev, -1); md_dev = margin(zdev)
        base_acc = (np.where(pt_dev < 5, pt_dev, -1) == ytr[dev]).mean()
        M = None
        for cand in np.unique(np.quantile(md_dev, np.linspace(0, 0.99, 100))):
            ph = np.where((pt_dev < 5) & (md_dev >= cand), pt_dev, pe_dev)
            if (ph == ytr[dev]).mean() >= base_acc - 0.01: M = cand; break
        M = M if M is not None else md_dev.max() + 1
        pt, pe, md = table_pred(zte), emb(zte), margin(zte); ph = np.where((pt < 5) & (md >= M), pt, pe); nw = yte >= 5
        for name, p in (("table(no new rows)", np.where(pt < 5, pt, -1)), ("embedding", pe), ("hybrid", ph)):
            rows[name].append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean()))
    for name, v in rows.items():
        a = np.mean(v, 0); print(f"NK={NK} k={k} {name:18s}: all-10 {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}", flush=True)
