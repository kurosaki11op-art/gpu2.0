"""Readout ceiling check (19 Oct 2026), a DIAGNOSTIC like the earlier readout ceilings, not a chip design: closed-form ridge regression to one-hot labels on the chip's own code (float, all data at once),
next to the slow-table chip learning the same data all at once. Tells whether the 5-bit counting readout still loses to a float linear readout on the same code. SIMULATED. usage: DATA_DIR; env DS, NPS."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
import detector_learn
D = sys.argv[1]; DS = os.environ.get("DS", "mnist"); NPS = int(os.environ.get("NPS", 2000)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
ctr, cte = enc(xtr).astype(np.float32), enc(xte).astype(np.float32); Y = np.eye(10, dtype=np.float32)[ytr]
mu = ctr.mean(0); A = ctr - mu; G = A.T @ A; B = A.T @ (Y - Y.mean(0))
for lam in (1.0, 10.0, 100.0, 1000.0):
    Wr = np.linalg.solve(G + lam * np.eye(G.shape[0], dtype=np.float32), B); print(DS, "ridge lambda", lam, "accuracy", round(float(((cte - mu) @ Wr).argmax(1).__eq__(yte).mean()), 4), flush=True)
