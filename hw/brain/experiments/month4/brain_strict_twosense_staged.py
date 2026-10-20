"""Does a second sense shrink the staged loss? (20 Oct 2026) SIMULATED. MNIST pictures + spoken digits (SET = fsdd: FSDD; sc: Speech Commands), classes learned in 5 stages of 2 digits, the chip's own dreams between stages (shipped rule: margin 256 / 1,500 dreams / 1 night). A seen digit is paired with a heard clip of the same digit.
Arms (staged vs one pass): picture alone; sound alone (new test speaker); both senses in one table, tested with both, with the picture alone (sound blank) and with the sound alone (picture blank). 3 seeds. usage: DATA_DIR SUBSET_DIR  (env SET)"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea, cochlea_int, detector_learn, cross_modal
from sound_features import SoundFeatures
from noise_floor import picture as _picture
from cortex_core import load
D, ROOT = sys.argv[1], sys.argv[2]; SET = os.environ.get("SET", "fsdd"); t0 = time.time(); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; SEEDS = 3
xtr, ytr, xte, yte = load(D, "mnist"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]; ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); venc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)]); vtr, vte = venc(xtr), venc(xte)
CHS = (50, 110, 170, ("on", 8))
if SET == "fsdd":
    z = np.load(os.path.join(D, "fsdd_framesums_int.npz")); S, sy, spk = z["S"], z["y"].astype(np.int64), z["spk"]; train_c = spk != spk.max(); test_c = spk == spk.max()
else:
    WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]; files, sy, spk = [], [], []
    for wi, w in enumerate(WORDS):
        for f in sorted(os.listdir(os.path.join(ROOT, w))): files.append(os.path.join(ROOT, w, f)); sy.append(wi); spk.append(int(f.split("_")[0], 16))
    sy = np.array(sy); grp = np.array(spk) % 5; X = np.stack([cochlea.read(p) for p in files]).astype(np.int16)
    S = np.concatenate([cochlea_int._bank(X[i:i + 500].astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, cochlea.FR, cochlea_int.FB) for i in range(0, len(X), 500)]); train_c = grp >= 1; test_c = grp == 0
pic = cochlea_int.align_word(_picture(S, "low4x4"), 6); sfs = [SoundFeatures(32, c, 3, 3, 1, 1, 4, 4).fit(pic[train_c][:12000]) for c in CHS]; A = np.concatenate([f.encode(pic) for f in sfs], 1)
tr_i, te_i = np.where(train_c)[0], np.where(test_c)[0]; acc = lambda m, c, y: float((m.predict(c) == y).mean()); R = {}


def run(code, labels, staged, seed):
    m = cross_modal.new_table(code.shape[1], seed)
    for i, s in enumerate(STAGES if staged else [tuple(range(10))]):
        o = np.where(np.isin(labels, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(code[o], labels[o])
    return m


for seed in range(1, SEEDS + 1):
    r = np.random.RandomState(seed); heard = A[np.array([r.choice(tr_i[sy[tr_i] == d]) for d in ytr])]; tp = np.array([r.choice(te_i[sy[te_i] == d]) for d in yte]); test_snd = A[tp]
    joint = np.concatenate([vtr, heard], 1)
    for staged in (False, True):
        tag = "staged" if staged else "one pass"
        R.setdefault("picture alone | " + tag, []).append(acc(run(vtr, ytr, staged, seed), vte, yte))
        R.setdefault("sound alone | " + tag, []).append(acc(run(heard, ytr, staged, seed), test_snd, yte))
        m = run(joint, ytr, staged, seed); z0 = np.zeros_like(heard[:len(yte)]); zp = np.zeros_like(vte)
        R.setdefault("both senses, tested with both | " + tag, []).append(acc(m, np.concatenate([vte, test_snd], 1), yte)); R.setdefault("both senses, tested with the picture only | " + tag, []).append(acc(m, np.concatenate([vte, z0], 1), yte)); R.setdefault("both senses, tested with the sound only | " + tag, []).append(acc(m, np.concatenate([zp, test_snd], 1), yte))
    print("seed", seed, "%.0fs" % (time.time() - t0), flush=True)
print("set", SET)
keys = sorted({k.split(" | ")[0] for k in R})
for k in keys: print("%-46s one pass %.4f  staged %.4f  (staged loss %.2f)" % (k, np.mean(R[k + " | one pass"]), np.mean(R[k + " | staged"]), 100 * (np.mean(R[k + " | one pass"]) - np.mean(R[k + " | staged"]))), flush=True)
