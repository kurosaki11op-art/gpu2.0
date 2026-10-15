"""Learning in noise: each training clip is heard once, either clean or with white noise at 20, 10 or 5 dB SNR (one
random condition per clip, fixed seed; PCLEAN = share of clean clips, default 0.25); detectors are learned from the same mixed pictures of stage 1. Tested on clean
and noisy test clips (same noise as noisy_sound.py). Integer cochlea with the 4x noise floor, exact integer chip model,
month-2 rule, 3 seeds. usage: DATA_DIR"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea, cochlea_int
from feature_layer import Features
from cortex_int import CortexInt
from noise_floor import picture, load_framesums  # noqa
D = sys.argv[1]; t0 = time.time(); MODE = "low4x4"
S, y, te = load_framesums(D)
root = os.path.join(D, "speech"); test = set(open(os.path.join(root, "testing_list.txt")).read().split())
X = []
for w in cochlea.WORDS:
    for f in sorted(os.listdir(os.path.join(root, w))):
        X.append(cochlea.read(os.path.join(root, w, f)))
X = np.stack(X)


def bank(x):
    return np.concatenate([cochlea_int._bank(x[i:i + 1000].astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G,
                                             cochlea.FR, cochlea_int.FB) for i in range(0, len(x), 1000)])


def add_noise(x, snr, g):
    p = (x ** 2).mean(1, keepdims=True); n = g.standard_normal(x.shape) * np.sqrt(p / 10 ** (snr / 10))
    return np.clip(np.round(x + n), -32768, 32767).astype(np.int16)


# test sets: identical to noisy_sound.py (same seed, same order)
Xte = X[te]; g = np.random.RandomState(12345); tests_S = {"clean": S[te]}
for snr in (20, 10, 5):
    tests_S[f"{snr}dB"] = bank(add_noise(Xte, snr, g))
# training clips: one random condition each
PCLEAN = float(os.environ.get("PCLEAN", "0.25"))                   # share of training clips heard clean
r = np.random.RandomState(777); Xtr = X[~te]; Str = S[~te].copy()
cond = np.where(r.random_sample(len(Xtr)) < PCLEAN, 0, 1 + r.randint(0, 3, len(Xtr)))
for k, snr in ((1, 20), (2, 10), (3, 5)):
    sel = np.where(cond == k)[0]
    Str[sel] = bank(add_noise(Xtr[sel], snr, np.random.RandomState(1000 + k)))
print("frame sums ready %.0fs" % (time.time() - t0), flush=True)
ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
xtr = picture(Str, MODE)
fes = [Features(64, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
ctr = enc(xtr); tests = {k: enc(picture(v, MODE)) for k, v in tests_S.items()}
accs = {k: [] for k in tests}
for seed in (1, 2, 3):
    m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
    for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
        sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
        m.stage(ctr[sel], ytr[sel])
    for k, c in tests.items():
        accs[k].append(float((m.predict(c) == yte).mean()))
res = {k: round(float(np.mean(v)), 4) for k, v in accs.items()}
print("trained in mixed noise, share clean", PCLEAN, res, "%.0fs" % (time.time() - t0), flush=True)
json.dump({"label": "SIMULATED (integer cochlea + 4x floor, exact integer chip model, 3 seeds)", "share_clean": PCLEAN, "trained_in_mixed_noise": res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"noisy_train_pclean{PCLEAN}.json"), "w"), indent=1)
