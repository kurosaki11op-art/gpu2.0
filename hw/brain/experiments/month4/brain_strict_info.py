"""Is the information in the code, or is the linear readout the limit? (20 Oct 2026) DIAGNOSTIC, SIMULATED. Same shipped code; float classifiers of increasing nonlinearity: linear ridge, kNN on overlap, RBF-style kernel ridge (kernel = exp(Hamming distance / s)). usage: DATA_DIR; env DS, NPS."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, detector_learn
from cortex_core import load
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); NPS = int(os.environ.get("NPS", 2000)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]; Y = np.eye(10, dtype=np.float32)[ytr]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)]).astype(np.float32)
a, b = enc(xtr), enc(xte); na, nb = a.sum(1), b.sum(1); ov = b @ a.T                      # overlap (popcount of AND)
ham = nb[:, None] + na[None, :] - 2 * ov
for k in (1, 5, 15):
    nn = np.argsort(ham, 1)[:, :k]; votes = np.zeros((len(b), 10)); [np.add.at(votes, (np.arange(len(b)), ytr[nn[:, j]]), 1) for j in range(k)]; print(DS, "kNN k=%d on Hamming" % k, round(float((votes.argmax(1) == yte).mean()), 4), flush=True)
Ka_med = np.median(ham)
for s in (0.25, 0.5, 1.0):
    sc = Ka_med * s; Ktr = np.exp(-(na[:, None] + na[None, :] - 2 * (a @ a.T)) / sc); Kte = np.exp(-ham / sc); best = 0
    for lam in (0.1, 1.0, 10.0):
        al = np.linalg.solve(Ktr + lam * np.eye(len(Ktr), dtype=np.float32), Y); best = max(best, float(((Kte @ al).argmax(1) == yte).mean()))
    print(DS, "kernel ridge (exp Hamming), scale %.2f x median" % s, round(best, 4), flush=True)
