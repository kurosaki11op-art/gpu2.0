"""Early exit (20 Oct 2026), SIMULATED. The brain recognises easy things from a first glance. The code is read channel by channel (4 retina channels); after each channel the chip compares the top-2 gap of the partial scores with a threshold chosen on the TRAINING examples (the smallest gap at which the partial winner agreed with the full winner on at least 99 % of
training examples); if the gap clears it the chip answers and the remaining channels are never read. Compares, adds and one threshold per step only. Chip: shipped settings (margin 256 / 1,500 dreams / 1 night), 5 stages, seed 1. Reports accuracy and the mean fraction of active bits read (= table reads per decision). usage: DATA_DIR; env DS."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; AG = float(os.environ.get("AGREE", 0.99))
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
ctr, cte = enc(xtr), enc(xte); NB = ctr.shape[1]; NC = len(fes); w = NB // NC
m = CortexSlow(NB, ch=100, K=5, night_stop=2, daydream=1, seed=1, margin=256, ndream=1500, night=1)
for i, s in enumerate(STAGES): o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
S = m.S.astype(np.int32); S[~m.known] = -(1 << 20)


def partial(code):                                   # cumulative score and cumulative active bits after each channel
    sc = np.zeros((len(code), len(S)), np.int64); cb = np.zeros(len(code)); out = []
    for k in range(NC):
        blk = code[:, k * w:(k + 1) * w].astype(np.int32); sc = sc + blk @ S[:, k * w:(k + 1) * w].T; cb = cb + blk.sum(1); out.append((sc.copy(), cb.copy()))
    return out


def gap(sc): o = np.sort(sc, 1); return o[:, -1] - o[:, -2]


ptr, pte = partial(ctr), partial(cte); full_tr = ptr[-1][0].argmax(1); full_te = pte[-1][0].argmax(1); th = []
for k in range(NC - 1):
    g = gap(ptr[k][0]); ag = ptr[k][0].argmax(1) == full_tr; cand = np.unique(np.percentile(g, np.arange(0, 100, 1))); t = cand[-1] + 1
    for c in cand:
        sel = g >= c
        if sel.sum() >= 20 and ag[sel].mean() >= AG: t = c; break
    th.append(t)
done = np.zeros(len(cte), bool); pred = np.zeros(len(cte), np.int64); read = np.zeros(len(cte)); tot = pte[-1][1]
for k in range(NC):
    sc, cb = pte[k]; ex = ~done & ((gap(sc) >= th[k]) if k < NC - 1 else True); pred[ex] = sc[ex].argmax(1); read[ex] = cb[ex]; done |= ex
print(DS, "full read: accuracy %.4f" % (full_te == yte).mean(), "| early exit: accuracy %.4f" % (pred == yte).mean(), "mean fraction of active bits read %.3f" % (read / np.maximum(tot, 1)).mean(), "thresholds", [int(t) for t in th], "channels at exit", np.bincount(np.argmax(np.stack([(~(np.arange(len(cte)) < 0)) for _ in range(1)]), 0) if False else np.zeros(1, int)).tolist() if False else "", flush=True)
