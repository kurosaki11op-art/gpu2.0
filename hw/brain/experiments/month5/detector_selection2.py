"""27 Oct 2026, SIMULATED. DEPLOYABLE VERSION of the detector-selection test. The first test (detector_selection.py) scored the 32 most informative of 128 detectors but kept the bits produced when all 128 compete at each position: a chip with only 32 detectors would see different winners, and reproducing those bits would need all 128 detectors evaluated per position (4x the front-end energy), so its cost claim (26.5 nJ) was wrong. Here the selected detectors are installed ALONE: the 128-detector pool is fitted, the K most informative are kept, and winner-take-all is recomputed among only those K, so the front end really runs K detectors per channel. Informative = counted mutual information between the pooled bit (from the 128-pool encoding, as before) and the class, summed over the 36 positions. Controls: K random of the pool (installed alone), and the shipped unsupervised K=32 fit (the reference 88.85).
env: POOLF, KS (comma list of K)."""
import os, sys, time, copy
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, ytr, xte, yte, train_table, CL, Features
E_ = lambda k, d: type(d)(os.environ.get(k, d)); POOLF = E_("POOLF", 128); KS = [int(v) for v in E_("KS", "32,64").split(",")]; SEED = E_("SEED", 0); NOCTRL = E_("NOCTRL", 0); t0 = time.time()
CH = [50, 150, ("on", 8), ("off", 8)]; K = 10
def mi_per_detector(codes, y, F):
    N = len(y); n1 = np.stack([codes[y == c].sum(0) for c in range(K)]).astype(np.float64); nc = np.bincount(y, minlength=K).astype(np.float64); n1t = n1.sum(0); mi = np.zeros(codes.shape[1])
    for c in range(K):
        for b in (0, 1):
            nb = (n1[c] if b else nc[c] - n1[c]); nbt = (n1t if b else N - n1t); pcb = (nb + 0.5) / (N + 1); mi += pcb * np.log(pcb / ((nc[c] / N) * ((nbt + 0.5) / (N + 1))))
    return mi.reshape(36, F).sum(0)
pools, scores = [], []
for c in CH:
    fe = Features(POOLF, seed=SEED, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]); pools.append(fe)
    sub = xtr[:20000]; a = np.concatenate([fe.encode(sub[i:i + 2000]) for i in range(0, len(sub), 2000)]).astype(np.uint8); scores.append(mi_per_detector(a, ytr[:20000], POOLF)); print("  channel %s: pool scored [%.0fs]" % (c, time.time() - t0), flush=True)
def subset(fe, idx):
    f2 = copy.copy(fe); f2.cnt = fe.cnt[idx].copy(); f2.F = len(idx); return f2
def run(tag, idxs):
    fes = [subset(pools[ch], idxs[ch]) for ch in range(4)]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for i in range(0, len(x), 2000)]) for g in fes], 1).astype(np.uint8)
    A, B = enc(xtr), enc(xte); W = train_table(A, ytr); S = B.astype(np.int32) @ W; p = S.argmax(1); mk = np.isin(yte, CL); s6 = S[:, 6] - np.delete(S, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("RESULT %-48s %5d bits, %4.0f active: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f [%.0fs]" % (tag, A.shape[1], B.sum(1).mean(), (p == yte).mean(), (CL[S[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap, time.time() - t0), flush=True)
rng = np.random.RandomState(0)
for k in KS:
    run("installed alone: %d most informative of %d" % (k, POOLF), [np.sort(np.argsort(-scores[ch])[:k]) for ch in range(4)])
    if not NOCTRL: run("installed alone: %d random of %d (control)" % (k, POOLF), [np.sort(rng.permutation(POOLF)[:k]) for ch in range(4)])
