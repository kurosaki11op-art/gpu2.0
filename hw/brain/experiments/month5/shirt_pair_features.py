"""25 Oct 2026 round 2, SIMULATED, Fashion-MNIST, single view, one seed. usage: python3 shirt_pair_features.py DATA_DIR [SMALL]
Idea 1: detectors learned from the confusable classes only (T-shirt, Pullover, Coat, Shirt), pooled 4 (A) and pooled 2 with 16 per channel (B), appended to L's 4,608-bit code.
Idea 2: thin-structure cue bits counted directly (thin vertical lines = placket, thin horizontal lines, silhouette width per row = sleeve and collar), appended to L's code.
Everything is read by L's counting table (CortexSlow). Matrix-free: patch matching, compares, counts."""
import sys, time
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
import feature_layer
from feature_layer import Features
D = sys.argv[1]; SMALL = len(sys.argv) > 2
xtr, ytr, xte, yte = load(D, "fashion"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
if SMALL: xtr, ytr, xte, yte = xtr[:8000], ytr[:8000], xte[:2000], yte[:2000]
CL = np.array([0, 2, 4, 6]); CH = (50, 150, ("on", 8), ("off", 8))
feature_layer.PS, feature_layer.ST = 5, 1
def enc_with(fes):
    return lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)]).astype(np.uint8)
t0 = time.time(); cl = np.isin(ytr, CL)
base = enc_with([Features(32, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH])
pairA = enc_with([Features(32, thr=c, pool=4).fit(xtr[cl][:12000]) for c in CH])
pairB = enc_with([Features(16, thr=c, pool=2).fit(xtr[cl][:12000]) for c in CH])
def cues(x):
    im = x.reshape(-1, 28, 28).astype(np.int16); out = []
    L = np.zeros_like(im); R = np.zeros_like(im); L[:, :, 1:] = im[:, :, :-1]; R[:, :, :-1] = im[:, :, 1:]
    for pol in (1, -1):                                              # thin vertical line, bright (1) or dark (-1) against both sides
        v = ((pol * (im - L) > 25) & (pol * (im - R) > 25))
        run = v[:, :-2] & v[:, 1:-1][:, :, :] & v[:, 2:] if False else (v[:, :-2, :] & v[:, 1:-1, :] & v[:, 2:, :])   # 3 rows long
        run = np.pad(run, ((0, 0), (1, 1), (0, 0)))
        out.append(run.reshape(len(im), 7, 4, 7, 4).any((2, 4)).reshape(len(im), -1))
    U = np.zeros_like(im); Dn = np.zeros_like(im); U[:, 1:] = im[:, :-1]; Dn[:, :-1] = im[:, 1:]
    h = ((im - U > 25) & (im - Dn > 25)); h = h[:, :, :-2] & h[:, :, 1:-1] & h[:, :, 2:]; h = np.pad(h, ((0, 0), (0, 0), (1, 1)))
    out.append(h.reshape(len(im), 7, 4, 7, 4).any((2, 4)).reshape(len(im), -1))
    fg = im > 40; width = fg.sum(2); first = np.where(fg.any(2), fg.argmax(2), 28); last = np.where(fg.any(2), 27 - fg[:, :, ::-1].argmax(2), 0)
    for t in range(4, 28, 3): out.append((width >= t))                  # width thermometer per row (sleeves, neck, hem)
    for t in range(4, 24, 5): out.append((first <= t)); out.append((last >= 27 - t))
    return np.concatenate([o.reshape(len(im), -1) for o in out], 1).astype(np.uint8)

def table(codes, labels):
    m = CortexSlow(codes.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); o = np.random.RandomState(100).permutation(len(labels)); m.stage(codes[o], labels[o]); return m.S.T.astype(np.int32)
def report(tag, nb, ctr, cte):
    sc = cte.astype(np.int32) @ table(ctr, ytr); p = sc.argmax(1); mk = np.isin(yte, CL); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s); tp = np.cumsum(yy[o])
    ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("%-44s bits %6d, active %5.0f | acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | %.0fs" % (tag, nb, ctr.sum(1).mean(), (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap, time.time() - t0), flush=True)
Ctr, Cte = base(xtr), base(xte); report("baseline L", Ctr.shape[1], Ctr, Cte)
for tag, f in (("+ pair detectors A (pool 4, 32/ch)", pairA), ("+ pair detectors B (pool 2, 16/ch)", pairB)):
    a, b = f(xtr), f(xte); report(tag, Ctr.shape[1] + a.shape[1], np.concatenate([Ctr, a], 1), np.concatenate([Cte, b], 1))
a, b = cues(xtr), cues(xte); report("+ thin-structure cues", Ctr.shape[1] + a.shape[1], np.concatenate([Ctr, a], 1), np.concatenate([Cte, b], 1))
