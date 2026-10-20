"""Fovea probe (20 Oct 2026) DIAGNOSTIC, SIMULATED. Does a fine look at the ambiguous place add information? Coarse code = shipped (5x5 patches, stride 2). Fine code = detectors over 3x3 patches at stride 1 (learned on the first stage, same chip rule), pooled 3x3.
Float dual-ridge ceiling on: coarse; coarse + full fine code (upper bound of any fovea); coarse + fine code masked to the cells where the top-2 rival classes' fine templates differ most (the fovea: 25 % of cells, chosen per image from the coarse top-2); coarse + fine code masked to random 25 % of cells (control).
usage: DATA_DIR; env DS, NPS."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import feature_layer, detector_learn
from cortex_core import load
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); NPS = int(os.environ.get("NPS", 2000)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; FR = float(os.environ.get("FRAC", 0.25))
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]; Y = np.eye(10, dtype=np.float32)[ytr]
first = xtr[np.isin(ytr, STAGES[0])]
fesc = detector_learn.learn_features(first); enc = lambda fs, x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fs], 1) for i in range(0, len(x), 1000)])
c_tr, c_te = enc(fesc, xtr), enc(fesc, xte)
feature_layer.PS, feature_layer.ST = 3, 1
from feature_layer import Features, patches, binarize
def learn_fine(x, chans=(50, 150, ("on", 8), ("off", 8)), F=32):
    out = []
    for c in chans:
        sd = detector_learn.StreamDetectors(F, nb=9); pp, _ = patches(binarize(x, c)); sd.learn(pp); sd.reseed()
        f = Features(F, thr=c); f.cnt = sd.cnt.copy(); out.append(f)
    return out
fesf = learn_fine(first)
for g in fesf: g.pool = 3
f_tr, f_te = enc(fesf, xtr), enc(fesf, xte); feature_layer.PS, feature_layer.ST = 5, 2
nch = len(fesf); F = fesf[0].F; m = f_tr.shape[1] // (nch * F); m = int(round(m ** 0.5)); print("coarse", c_tr.shape, "fine", f_tr.shape, "fine map", m, flush=True)


def ridge(a, b, lams=(100.0, 300.0, 1000.0), pred=False):
    a = a.astype(np.float32); b = b.astype(np.float32); mu = a.mean(0); A = a - mu; Kt = A @ A.T; Kte = (b - mu) @ A.T; best = (0, None)
    for lam in lams:
        al = np.linalg.solve(Kt + lam * np.eye(len(Kt), dtype=np.float32), Y - Y.mean(0)); s = Kte @ al; acc = float((s.argmax(1) == yte).mean())
        if acc > best[0]: best = (acc, s)
    return best if pred else best[0]


acc_c, s_c = ridge(c_tr, c_te, pred=True); print(DS, "coarse alone", round(acc_c, 4), flush=True)
print(DS, "coarse + full fine", round(ridge(np.concatenate([c_tr, f_tr], 1), np.concatenate([c_te, f_te], 1)), 4), "(%d bits)" % (c_tr.shape[1] + f_tr.shape[1]), flush=True)
print(DS, "fine alone", round(ridge(f_tr, f_te), 4), flush=True)
cells = lambda f: f.reshape(len(f), nch, m * m, F)                      # fine code as (image, channel, cell, feature)
ft, fe = cells(f_tr), cells(f_te); mean = np.stack([ft[ytr == c].mean(0) for c in range(10)])    # class templates (10, nch, cells, F)
top2 = np.argsort(-s_c, 1)[:, :2]; K = max(1, int(FR * m * m))


def masked(f, a, b, rnd=False):
    out = np.zeros_like(f); g = np.random.RandomState(3)
    for i in range(len(f)):
        if rnd: sel = g.permutation(m * m)[:K]
        else:
            d = np.abs(mean[a[i]] - mean[b[i]]).sum((0, 2)); sel = np.argsort(-d)[:K]                    # cells where the two rival templates differ most (sum of absolute differences, adds only)
        out[i][:, sel] = f[i][:, sel]
    return out.reshape(len(f), -1)


# train side: for each training image use its true class and the best rival under the coarse readout as the pair (the pair the chip would meet on a surprise)
a_tr = ytr.copy(); sc_tr = ridge(c_tr, c_tr, pred=True)[1]; sc_tr[np.arange(len(ytr)), ytr] = -1e9; b_tr = sc_tr.argmax(1)
for name, rnd in (("fovea (rival-template cells, 25 %)", False), ("random cells (control, 25 %)", True)):
    mtr = masked(ft, a_tr, b_tr, rnd); mte = masked(fe, top2[:, 0], top2[:, 1], rnd)
    print(DS, "coarse + " + name, round(ridge(np.concatenate([c_tr, mtr], 1), np.concatenate([c_te, mte], 1)), 4), flush=True)
