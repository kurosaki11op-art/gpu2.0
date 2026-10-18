"""Save sound codes for a geometry spec (ph,pw,sy,sx,py,px,F; sound_features.SoundFeatures), detectors fitted on SC words 0-1, aligned pictures: SC train / test and FSDD -> DATA_DIR/word_codes_<tag>.npz. usage: DATA_DIR spec tag"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from sound_features import SoundFeatures
from sound_align_confirm import align
D, spec, tag = sys.argv[1], sys.argv[2], sys.argv[3]
ph, pw, sy, sx, py, px, F = [int(v) for v in spec.split(",")]
f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]; ytr = y[~te].astype(int); P = align(S, 6); xtr, xte = P[~te], P[te]
fs = np.load(os.path.join(D, "fsdd_framesums_int.npz")); xfs = align(fs["S"], 6)
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
fes = [SoundFeatures(F, c, ph, pw, sy, sx, py, px).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
enc = lambda x: np.concatenate([np.concatenate([q.encode(x[i:i + 2000]) for q in fes], 1) for i in range(0, len(x), 2000)])
np.savez_compressed(os.path.join(D, f"word_codes_{tag}.npz"), tr=enc(xtr), te=enc(xte), fs=enc(xfs), yfs=fs["y"]); print("saved", tag)
