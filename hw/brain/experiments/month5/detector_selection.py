"""27 Oct 2026, SIMULATED. LEARN WHAT IS COMMON AND UNCOMMON: choose L's detectors by how well they tell the classes apart. L's detectors are learned without labels (Hebbian winner-take-all, 32 per channel). Here each channel gets an OVERCOMPLETE pool of 128 Hebbian detectors (same recipe), and the 32 per channel with the highest class information are kept: the information is the mutual information between each detector's pooled bit (at each of the 36 window positions) and the class label, summed over positions, computed from counts only (no multiply in the chip; the scoring is done once, at learning time). The chip runs exactly as many detectors as today (32 per channel, 4,608 bits), so front-end and table cost are unchanged.
Compared on the same table: (a) shipped unsupervised 32 per channel (88.85), (b) the whole pool of 128 per channel (4x the bits and front-end cost: an upper bound for this idea), (c) the 32 most informative of the 128, (d) 32 random of the 128 (control: selection must beat chance), (e) 32 least informative (sanity).
env: POOLF (pool size per channel), KEEP."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, ytr, xte, yte, train_table, CL, Features
E_ = lambda k, d: type(d)(os.environ.get(k, d)); POOLF = E_("POOLF", 128); KEEP = E_("KEEP", 32); t0 = time.time()
CH = [50, 150, ("on", 8), ("off", 8)]; K = 10
def mi_per_detector(codes, y, F, K=10):                                                                      # codes (N, 36*F) bits; score per detector = sum over the 36 positions of MI(bit; class)
    N = len(y); n1 = np.stack([codes[y == c].sum(0) for c in range(K)]).astype(np.float64); nc = np.bincount(y, minlength=K).astype(np.float64); n1t = n1.sum(0)
    mi = np.zeros(codes.shape[1])
    for c in range(K):
        for b in (0, 1):
            nb = (n1[c] if b else nc[c] - n1[c]); nbt = (n1t if b else N - n1t); pcb = (nb + 0.5) / (N + 1); mi += pcb * np.log(pcb / ((nc[c] / N) * ((nbt + 0.5) / (N + 1))))
    return mi.reshape(36, F).sum(0)
pool_tr, pool_te, scores, gscores = [], [], [], []
GRP = np.array([0, 2, 4, 6]); gm = np.isin(ytr, GRP); gy = np.searchsorted(GRP, ytr[gm])
for c in CH:
    fe = Features(POOLF, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000])
    enc = lambda x: np.concatenate([fe.encode(x[i:i + 2000]) for i in range(0, len(x), 2000)]).astype(np.uint8)
    a, b = enc(xtr), enc(xte); pool_tr.append(a); pool_te.append(b); scores.append(mi_per_detector(a, ytr, POOLF)); gscores.append(mi_per_detector(a[gm], gy, POOLF, 4)); print("  channel %s: pool of %d detectors encoded, information per detector min %.3f median %.3f max %.3f [%.0fs]" % (c, POOLF, scores[-1].min(), np.median(scores[-1]), scores[-1].max(), time.time() - t0), flush=True)
def pick(which, Fsel, rng=np.random.RandomState(0)):
    cols = []
    for ch in range(4):
        order = np.argsort(-scores[ch]) if which == "top" else np.argsort(scores[ch]) if which == "bottom" else rng.permutation(POOLF)
        cols.append(np.sort(order[:Fsel]))
    return cols
def build(cols, w):
    src = pool_tr if w == 0 else pool_te
    return np.concatenate([src[ch].reshape(len(src[ch]), 36, POOLF)[:, :, cols[ch]].reshape(len(src[ch]), -1) for ch in range(4)], 1)
def run(tag, cols):
    A, B = build(cols, 0), build(cols, 1); W = train_table(A, ytr); S = B.astype(np.int32) @ W; p = S.argmax(1); mk = np.isin(yte, CL); s6 = S[:, 6] - np.delete(S, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("RESULT %-52s %5d bits, %4.0f active: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f [%.0fs]" % (tag, A.shape[1], B.sum(1).mean(), (p == yte).mean(), (CL[S[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap, time.time() - t0), flush=True)
run("(b) whole pool, %d per channel (upper bound, 4x cost)" % POOLF, [np.arange(POOLF)] * 4)
run("(c) the %d most informative of %d" % (KEEP, POOLF), pick("top", KEEP)); run("(d) %d random of %d (control)" % (KEEP, POOLF), pick("rand", KEEP)); run("(e) the %d least informative (sanity)" % KEEP, pick("bottom", KEEP))
run("    the 16 most informative", pick("top", 16)); run("    the 64 most informative (2x cost)", pick("top", 64))

def group_extra(nglobal, nextra):                                                                      # global top nglobal, plus the nextra most informative WITHIN the confusable group that are not already chosen
    cols = []
    for ch in range(4):
        g = list(np.argsort(-scores[ch])[:nglobal]); extra = [f for f in np.argsort(-gscores[ch]) if f not in g][:nextra]; cols.append(np.sort(np.array(g + extra)))
    return cols
run("32 global + 16 group-informative (48 per channel)", group_extra(32, 16)); run("48 global (control for the same detector count)", pick("top", 48))
run("32 global + 32 group-informative (64 per channel)", group_extra(32, 32)); run("group-informative only, top 32 per channel", [np.sort(np.argsort(-gscores[ch])[:32]) for ch in range(4)])
