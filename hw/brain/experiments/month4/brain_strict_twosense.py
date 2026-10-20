"""Two senses (20 Oct 2026) SIMULATED. Vision = MNIST digits through the shipped retina code (4,608 bits); hearing = FSDD spoken digits (zero..nine, 6 speakers, 8 kHz) through the integer cochlea, noise floor, word alignment and the sound detector rule (10 channels, 23,040 bits). The two sets share only the digit class; a seen digit is paired with a heard clip of the same digit
(different instances, as a child sees a shirt while hearing the word). Chip: counting table, one pass, margin 256 / 1,500 dreams / 1 night, 3 seeds. Test speaker = the last speaker (not in training).
  A  picture learner with the TRUE labels (reference)
  B  picture learner with ZERO labels: each seen digit's label is what the ear's own classifier (trained on the labelled sound clips) says about the clip heard with it
  C  sound learner alone (labelled clips), test on the held-out speaker
  D  joint table over picture + sound bits, trained on the pairs; tested with both senses, picture only (sound blank), sound only (picture blank), and with a degraded sense: 25 % of the picture's active bits dropped, or 50 % of the sound's
usage: DATA_DIR; env NPS, SEEDS."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea_int, detector_learn
from sound_features import SoundFeatures
from noise_floor import picture as _picture
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 3)); t0 = time.time(); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, "mnist"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
vtr, vte = enc(xtr), enc(xte)
z = np.load(os.path.join(D, "fsdd_framesums_int.npz")); S, sy, spk = z["S"], z["y"].astype(np.int64), z["spk"]; stest = spk == spk.max()
pic = cochlea_int.align_word(_picture(S, "low4x4"), 6); CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
fs = [SoundFeatures(64, c, 3, 3, 1, 1, 4, 4).fit(pic[~stest][:12000]) for c in CH]; aenc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 1000]) for f in fs], 1) for i in range(0, len(x), 1000)])
atr, ate = aenc(pic[~stest]), aenc(pic[stest]); satr, sate = sy[~stest], sy[stest]; print("vision", vtr.shape, "hearing", atr.shape, "train clips", len(satr), "test clips", len(sate), "%.0fs" % (time.time() - t0), flush=True)


def chip(nb, seed): return CortexSlow(nb, ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)


def fit(code, lab, seed):
    m = chip(code.shape[1], seed); o = np.random.RandomState(seed).permutation(len(lab)); m.stage(code[o], lab[o]); return m


acc = lambda m, c, y: float((m.predict(c) == y).mean())
R = {k: [] for k in ("B2 picture, labels from an ear that never heard these speakers", "  B2 ear's label accuracy on those clips", "A picture, true labels", "B picture, labels from the ear (zero picture labels)", "  ear's label accuracy on the clips paired", "C sound alone (new speaker)", "D both senses", "D picture only", "D sound only", "D picture 25% dropped + sound", "D picture + sound 50% dropped", "D picture 25% dropped, sound blank", "D sound 50% dropped, picture blank")}
for seed in range(1, SEEDS + 1):
    r = np.random.RandomState(seed); ear = fit(atr, satr, seed); R["C sound alone (new speaker)"].append(acc(ear, ate, sate))
    pair = np.array([r.choice(np.where(satr == d)[0]) for d in ytr]); heard = atr[pair]; said = ear.predict(heard)                  # a clip of the same digit is heard with every picture
    R["  ear's label accuracy on the clips paired"].append(float((said == ytr).mean()))
    sp = spk[~stest]; ear2 = fit(atr[sp <= 2], satr[sp <= 2], seed); pool = np.where(sp >= 3)[0]; pair2 = np.array([r.choice(pool[satr[pool] == d]) for d in ytr]); said2 = ear2.predict(atr[pair2])        # honest version: the ear learned from speakers 0-2; the clips heard with the pictures are from speakers 3-4 it never heard
    R["B2 picture, labels from an ear that never heard these speakers"].append(acc(fit(vtr, said2, seed), vte, yte)); R["  B2 ear's label accuracy on those clips"].append(float((said2 == ytr).mean()))
    R["A picture, true labels"].append(acc(fit(vtr, ytr, seed), vte, yte)); R["B picture, labels from the ear (zero picture labels)"].append(acc(fit(vtr, said, seed), vte, yte))
    joint = fit(np.concatenate([vtr, heard], 1), ytr, seed); tp = np.array([r.choice(np.where(sate == d)[0]) for d in yte]); tsound = ate[tp]
    drop = lambda c, p: c & (r.rand(*c.shape) >= p); blank_v, blank_a = np.zeros_like(vte), np.zeros_like(tsound)
    for k, (v, a) in {"D both senses": (vte, tsound), "D picture only": (vte, blank_a), "D sound only": (blank_v, tsound), "D picture 25% dropped + sound": (drop(vte, .25), tsound), "D picture + sound 50% dropped": (vte, drop(tsound, .5)),
                      "D picture 25% dropped, sound blank": (drop(vte, .25), blank_a), "D sound 50% dropped, picture blank": (blank_v, drop(tsound, .5))}.items(): R[k].append(acc(joint, np.concatenate([v, a], 1), yte))
    print("seed", seed, "%.0fs" % (time.time() - t0), flush=True)
for k, v in R.items(): print("%-58s %.4f" % (k, np.mean(v)), flush=True)
