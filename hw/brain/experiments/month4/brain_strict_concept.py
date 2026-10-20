"""Concept cells on today's code (20 Oct 2026), SIMULATED. Per-class prototype cells (ConceptMemory: each class owns P cells, learning a class touches only its own cells), so learning in stages equals learning all at once by construction.
Same shipped coarse code and test set as the chip runs. usage: DATA_DIR; env DS, NPS."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import detector_learn
from feature_layer import ConceptMemory
from cortex_core import load
D = sys.argv[1]; DS = os.environ.get("DS", "fashion"); NPS = int(os.environ.get("NPS", 2000)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
ctr, cte = enc(xtr), enc(xte)
for P in (4, 16, 32):
    m = ConceptMemory(ctr.shape[1], 10, P=P, seed=1)
    for s in STAGES: o = np.where(np.isin(ytr, s))[0]; m.learn(ctr[o], ytr[o])
    print(DS, "concept cells P=%d (staged = once)" % P, "accuracy %.4f" % float((m.predict(cte) == yte).mean()), "cells x bits = %d" % (10 * P * ctr.shape[1]), "%.0fs" % (time.time() - t0), flush=True)
