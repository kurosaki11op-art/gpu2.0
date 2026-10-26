"""26 Oct 2026, SIMULATED. PART 5, first test (cheapest design): does a RELATION between two parts generalise to unseen classes? Task: given two clothing images (L's 4,608-bit detector codes), say whether they are the same class. Train pairs come only from classes 0-5; test pairs from the 4 unseen classes (6-9) and, for reference, from seen classes.
Features compared (all counted by L's own margin-trained counting table, 2 outputs same/different, no multiply):
 relation: bits where both images are on (x AND y) and bits where exactly one is on (x XOR y): an XNOR-style agreement code that does not name the class;
 concat:   [x, y] side by side (the table can only memorise which classes go together; no relation);
 overlap:  one number, |x AND y|, thresholded on training pairs (no learning of structure).
env: NTR training pairs."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table
NTR = int(os.environ.get("NTR", 60000)); rs = np.random.RandomState(0)
def pairs(C, y, classes, n):
    idx = [np.where(np.isin(y, [c]))[0] for c in classes]; a = np.zeros(n, int); b = np.zeros(n, int); lab = np.zeros(n, int)
    for i in range(n):
        if i % 2 == 0: c = rs.randint(len(classes)); a[i], b[i] = rs.choice(idx[c], 2, replace=False); lab[i] = 1
        else: c1, c2 = rs.choice(len(classes), 2, replace=False); a[i], b[i] = rs.choice(idx[c1]), rs.choice(idx[c2]); lab[i] = 0
    return a, b, lab
def feats(C, a, b, kind):
    x, y_ = C[a], C[b]
    if kind == "relation": return np.concatenate([x & y_, x ^ y_], 1)
    if kind == "concat": return np.concatenate([x, y_], 1)
    if kind in ("pooled_detector", "pooled_position", "pooled_both"):                                      # class-agnostic: agreement counts pooled over positions (per detector) or over detectors (per position), as thermometer bins
        g = lambda M: M.reshape(len(M), 4, 6, 6, 32)
        both, xr = g(x & y_).astype(np.int16), g(x ^ y_).astype(np.int16); parts = []
        if kind in ("pooled_detector", "pooled_both"): parts += [both.sum((2, 3)).reshape(len(x), -1), xr.sum((2, 3)).reshape(len(x), -1)]
        if kind in ("pooled_position", "pooled_both"): parts += [both.sum((1, 4)).reshape(len(x), -1), xr.sum((1, 4)).reshape(len(x), -1)]
        M = np.concatenate(parts, 1); th = np.array([1, 2, 3, 5, 8, 12, 18, 26]); return (M[:, :, None] >= th[None, None, :]).reshape(len(x), -1).astype(np.uint8)
SEEN, UNSEEN = [0, 1, 2, 3, 4, 5], [6, 7, 8, 9]
atr, btr, ltr = pairs(ctr, ytr, SEEN, NTR); sets = {"seen classes": pairs(cte, yte, SEEN, 20000), "UNSEEN classes": pairs(cte, yte, UNSEEN, 20000)}
for kind in ("relation", "concat", "pooled_detector", "pooled_position", "pooled_both"):
    W = train_table(feats(ctr, atr, btr, kind).astype(np.uint8), ltr)
    for nm, (a, b, l) in sets.items():
        sc = feats(cte, a, b, kind).astype(np.int32) @ W; p = sc.argmax(1); print("RESULT %-9s %-15s accuracy %.4f (chance 0.5)" % (kind, nm, (p == l).mean()), flush=True)
ov = lambda C, a, b: (C[a] & C[b]).sum(1); o = ov(ctr, atr, btr); ths = np.unique(np.quantile(o, np.linspace(0.05, 0.95, 60))); th = ths[np.argmax([((o >= t) == ltr).mean() for t in ths])]
for nm, (a, b, l) in sets.items(): print("RESULT overlap   %-15s accuracy %.4f (threshold %.0f chosen on seen training pairs)" % (nm, ((ov(cte, a, b) >= th) == l).mean(), th), flush=True)
