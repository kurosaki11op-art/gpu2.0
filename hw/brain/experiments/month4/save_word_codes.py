"""Save the shipped sound codes (detectors fitted on words 0-1, aligned pictures) of Speech Commands train / test and of the FSDD digits to DATA_DIR/word_codes_shipped.npz (tr, te, fs)
so that experiments on 'more words' do not have to re-encode. usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from feature_layer import Features
from sound_align_confirm import align
D = sys.argv[1]
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); fs = np.load(os.path.join(D, "fsdd_framesums_int.npz"))
f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]; ytr = y[~te].astype(int)
xtr = align(S, 6)[~te]; xfs = align(fs["S"], 6)
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
fes = [Features(64, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
enc = lambda x: np.concatenate([np.concatenate([q.encode(x[i:i + 2000]) for q in fes], 1) for i in range(0, len(x), 2000)])
cfs = enc(xfs); np.savez_compressed(os.path.join(D, "word_codes_shipped.npz"), tr=z["tr"], te=z["te"], fs=cfs, yfs=fs["y"]); print("saved", cfs.shape, "(tr/te taken from sep_speech_align_F64_p2.npz, same detectors)")
