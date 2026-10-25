"""25 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. MEM-C1: store only what differs between classes, then prune and share codes.
Every table row (one detector bit, 10 class values) can be shifted by any constant without changing which class wins, so the part common to all classes is removed (row centred on its median). What is left is the DIFFERENCE between classes. Small differences are pruned, the rest are stored as (class index, b-bit code) pairs in a compressed row; a decision reads only the rows of the active bits and only their kept entries.
Cost model (counts, not energy): bits read per decision = sum over active bits of (kept entries x (4 bits class index + b bits code) + 8 bits row pointer); dense reference = active bits x 10 entries x b bits. Table bytes = the same sum over all 4,608 rows.
env: none. Reference L: dense table, 578 active bits per image."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, CL
W = train_table(ctr, ytr).astype(np.float64); NB = W.shape[0]; act = cte[:2000].sum(1).mean()
def metrics(sc):
    p = sc.argmax(1); mk = np.isin(yte, CL); s6 = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    return (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), ap
Xte = cte.astype(np.float32)
a, c, ap = metrics(Xte @ W.astype(np.float32)); print("dense table, full precision: acc %.4f | cluster %.4f | Shirt AP %.3f | table values range %.0f to %.0f" % (a, c, ap, W.min(), W.max()))
Wc = W - np.median(W, axis=1, keepdims=True)                                                                  # remove what is common to all classes
a, c, ap = metrics(Xte @ Wc.astype(np.float32)); print("centred rows (should equal dense): acc %.4f | Shirt AP %.3f | non-zero entries %.1f%%" % (a, ap, 100 * (Wc != 0).mean()))
nz_tot = (np.abs(Wc) > 0).sum(1)
print("%-9s %-11s %-9s | %-8s %-8s %-8s | %-18s %-18s %-12s" % ("bits", "kept", "entries", "acc", "cluster", "ShirtAP", "bits read/decision", "dense b-bit reads", "table bytes"))
for b in (2, 3, 4):
    q = (1 << (b - 1)) - 1
    for keep in (1.0, 0.5, 0.3, 0.2, 0.1):
        thr = np.quantile(np.abs(Wc[Wc != 0]), 1 - keep) if keep < 1 else 0
        M = np.where(np.abs(Wc) >= thr, Wc, 0.0); scale = np.abs(M).max() / q; Q = np.round(M / scale).clip(-q, q); kept = (Q != 0)
        a, c, ap = metrics(Xte @ Q.astype(np.float32)); per_row = kept.sum(1); mean_rows = (Xte[:2000] @ per_row).mean()
        bits_read = mean_rows * (4 + b) + act * 8; dense = act * 10 * b; tab_bytes = (per_row.sum() * (4 + b) + NB * 8) / 8
        print("%-9d %-11.2f %-9d | %-8.4f %-8.4f %-8.3f | %-18.0f %-18.0f %-12.0f" % (b, keep, kept.sum(), a, c, ap, bits_read, dense, tab_bytes))
