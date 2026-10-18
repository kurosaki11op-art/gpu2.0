"""Save the finer-grid (stride 1, pool 4) image codes: sep_{DS}_s1_F32.npz with tr / te (4,608 bits), channels as shipped, detectors fitted on classes 0-1. usage: DATA_DIR DS"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, feature_layer
from feature_layer import Features
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
feature_layer.PS, feature_layer.ST = 5, 1
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64)
fes = [Features(32, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)])
np.savez_compressed(os.path.join(D, f"sep_{DS}_s1_F32.npz"), tr=enc(xtr), te=enc(xte)); print("saved", DS)
