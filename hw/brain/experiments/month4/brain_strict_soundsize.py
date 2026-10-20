"""How small can the sound code be? (20 Oct 2026) SIMULATED. FSDD spoken digits through the integer cochlea; sound code variants: number of detectors per spot (F) and which channels. For each: bits, sound-alone accuracy on the held-out speaker (counting table, one pass, margin 256 / 1,500 dreams / 1 night), and the both-senses accuracy with MNIST pictures (joint table, picture + paired clip). 3 seeds. usage: DATA_DIR"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea_int, detector_learn
from sound_features import SoundFeatures
from noise_floor import picture as _picture
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; t0 = time.time(); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, "mnist"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]; ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); venc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)]); vtr, vte = venc(xtr), venc(xte)
z = np.load(os.path.join(D, "fsdd_framesums_int.npz")); S, sy, spk = z["S"], z["y"].astype(np.int64), z["spk"]; stest = spk == spk.max(); pic = cochlea_int.align_word(_picture(S, "low4x4"), 6); satr, sate = sy[~stest], sy[stest]
ALLCH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
VARIANTS = [("10 channels x 64 detectors (shipped)", ALLCH, 64), ("10 x 32", ALLCH, 32), ("10 x 16", ALLCH, 16), ("5 channels x 64", (50, 110, 170, 230, ("on", 8)), 64), ("5 x 32", (50, 110, 170, 230, ("on", 8)), 32), ("4 x 32", (50, 110, 170, ("on", 8)), 32), ("3 x 32", (80, 170, ("on", 8)), 32), ("3 x 16", (80, 170, ("on", 8)), 16)]


def fit(code, lab, seed):
    m = CortexSlow(code.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1); o = np.random.RandomState(seed).permutation(len(lab)); m.stage(code[o], lab[o]); return m


for name, chs, F in VARIANTS:
    fs = [SoundFeatures(F, c, 3, 3, 1, 1, 4, 4).fit(pic[~stest][:12000]) for c in chs]; aenc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 1000]) for f in fs], 1) for i in range(0, len(x), 1000)])
    atr, ate = aenc(pic[~stest]), aenc(pic[stest]); sa, jo = [], []
    for seed in (1, 2, 3):
        r = np.random.RandomState(seed); sa.append(float((fit(atr, satr, seed).predict(ate) == sate).mean()))
        heard = atr[np.array([r.choice(np.where(satr == d)[0]) for d in ytr])]; joint = fit(np.concatenate([vtr, heard], 1), ytr, seed); tp = np.array([r.choice(np.where(sate == d)[0]) for d in yte])
        jo.append(float((joint.predict(np.concatenate([vte, ate[tp]], 1)) == yte).mean()))
    print("%-38s sound bits %6d  picture+sound bits %6d | sound alone %.4f | both senses %.4f | %.0fs" % (name, atr.shape[1], atr.shape[1] + vtr.shape[1], np.mean(sa), np.mean(jo), time.time() - t0), flush=True)
