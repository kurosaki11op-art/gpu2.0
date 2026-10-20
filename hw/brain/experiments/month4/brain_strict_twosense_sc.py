"""Two senses on a SECOND dataset pair (20 Oct 2026) SIMULATED: MNIST pictures + Speech Commands spoken digits (one..nine, zero; 100 clips each, many speakers, varied microphones: noisier than FSDD). Speakers (hash mod 5): 1-2 teach the ear (labelled clips), 3-4 are heard with the pictures (the ear names them), 0 is the test speaker.
Same chip rule and sound code as brain_strict_twosense*.py (4 channels x 32 detectors, 4,608 bits). Arms: ear alone on the test speaker; picture learner with true labels; with the ear's names as given (zero picture labels); with the names cleaned in sleep (neighbour pooling K = 8, buffer 256, ear vote, 2 rounds); both senses in one table (labelled pairs). 3 seeds. usage: DATA_DIR SUBSET_DIR"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea, cochlea_int, detector_learn, cross_modal
from sound_features import SoundFeatures
from noise_floor import picture as _picture
from cortex_core import load
D, ROOT = sys.argv[1], sys.argv[2]; t0 = time.time(); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; SEEDS = 3
WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
xtr, ytr, xte, yte = load(D, "mnist"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]; ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); venc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)]); vtr, vte = venc(xtr), venc(xte)
files, sy, spk = [], [], []
for wi, w in enumerate(WORDS):
    for f in sorted(os.listdir(os.path.join(ROOT, w))): files.append(os.path.join(ROOT, w, f)); sy.append(wi); spk.append(int(f.split("_")[0], 16))
sy = np.array(sy); grp = np.array(spk) % 5; X = np.stack([cochlea.read(p) for p in files]).astype(np.int16)
S = np.concatenate([cochlea_int._bank(X[i:i + 500].astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, cochlea.FR, cochlea_int.FB) for i in range(0, len(X), 500)])
pic = cochlea_int.align_word(_picture(S, "low4x4"), 6); CHS = (50, 110, 170, ("on", 8))
sfs = [SoundFeatures(32, c, 3, 3, 1, 1, 4, 4).fit(pic[(grp >= 1)][:12000]) for c in CHS]; aenc = lambda x: np.concatenate([f.encode(x) for f in sfs], 1); A = aenc(pic)
ear_i, pool_i, test_i = np.where(np.isin(grp, (1, 2)))[0], np.where(np.isin(grp, (3, 4)))[0], np.where(grp == 0)[0]
print("clips: ear-teaching %d, paired %d, test %d; sound code %d bits; picture code %d bits | %.0fs" % (len(ear_i), len(pool_i), len(test_i), A.shape[1], vtr.shape[1], time.time() - t0), flush=True)
acc = lambda m, c, y: float((m.predict(c) == y).mean()); R = {}
for seed in range(1, SEEDS + 1):
    r = np.random.RandomState(seed); ear = cross_modal.fit(A[ear_i], sy[ear_i], seed); R.setdefault("ear alone, unseen test speakers", []).append(acc(ear, A[test_i], sy[test_i]))
    pair = np.array([r.choice(pool_i[sy[pool_i] == d]) for d in ytr]); names = ear.predict(A[pair]); R.setdefault("ear's names right on the clips heard with the pictures", []).append(float((names == ytr).mean()))
    R.setdefault("A picture learner, true labels", []).append(acc(cross_modal.fit(vtr, ytr, seed), vte, yte)); R.setdefault("B picture learner, ear's names as given (zero picture labels)", []).append(acc(cross_modal.fit(vtr, names, seed), vte, yte))
    m, lab = cross_modal.learn_picture(vtr, names, rounds=2, seed=seed); R.setdefault("B+ picture learner, names cleaned in sleep", []).append(acc(m, vte, yte)); R.setdefault("  cleaned names right", []).append(float((lab == ytr).mean()))
    allp = np.where(grp >= 1)[0]; pair2 = np.array([r.choice(allp[sy[allp] == d]) for d in ytr]); joint = cross_modal.fit(np.concatenate([vtr, A[pair2]], 1), ytr, seed); tp = np.array([r.choice(test_i[sy[test_i] == d]) for d in yte])
    R.setdefault("D both senses in one table", []).append(acc(joint, np.concatenate([vte, A[tp]], 1), yte)); R.setdefault("D picture 25% dropped + sound", []).append(acc(joint, np.concatenate([vte & (r.rand(*vte.shape) >= .25), A[tp]], 1), yte)); R.setdefault("D picture 25% dropped, sound blank", []).append(acc(joint, np.concatenate([vte & (r.rand(*vte.shape) >= .25), np.zeros_like(A[tp])], 1), yte))
    print("seed", seed, "%.0fs" % (time.time() - t0), flush=True)
for k, v in R.items(): print("%-62s %.4f" % (k, np.mean(v)), flush=True)
