"""Word alignment in noise (does the loudness-based word start survive noise?). As noisy_sound.py, modes:
low4x4 (noise floor, today before alignment) and low4x4_align (floor + cochlea_int.align_word, lead 6).
Original description: Robustness to background noise: the chip learns the 10 words from clean clips (5 stages, month-2 rule) and is tested
on the test clips with white noise added at 20, 10 and 5 dB SNR (fixed noise seed). Cochlea front ends compared: no
noise removal, the noise floor (4x mean of the 4 quietest frames), and the floor plus a gate (MODES). Integer cochlea,
exact integer chip model, 3 seeds. usage: DATA_DIR [modes]"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea, cochlea_int
from feature_layer import Features
from cortex_int import CortexInt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from noise_floor import picture as _picture  # noqa  (same picture() as the floor / gate experiments)


def picture(S, mode):
    if mode.endswith("_align"):
        return cochlea_int.align_word(_picture(S, mode[:-6]), 6)
    return _picture(S, mode)
D = sys.argv[1]; MODES = ["low4x4", "low4x4_align"]; t0 = time.time()
z = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = z["S"], z["y"], z["te"]
root = os.path.join(D, "speech"); test = set(open(os.path.join(root, "testing_list.txt")).read().split())
# raw test clips, in the same order as the frame sums
Xte = []
for w in cochlea.WORDS:
    for f in sorted(os.listdir(os.path.join(root, w))):
        if f"{w}/{f}" in test:
            Xte.append(cochlea.read(os.path.join(root, w, f)))
Xte = np.stack(Xte); g = np.random.RandomState(12345)
noisy = {}
for snr in (20, 10, 5):
    p = (Xte ** 2).mean(1, keepdims=True); n = g.standard_normal(Xte.shape) * np.sqrt(p / 10 ** (snr / 10))
    xn = np.clip(np.round(Xte + n), -32768, 32767).astype(np.int16)
    noisy[snr] = np.concatenate([cochlea_int._bank(xn[i:i + 1000].astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G,
                                                   cochlea.FR, cochlea_int.FB) for i in range(0, len(xn), 1000)])
print("noisy frame sums ready %.0fs" % (time.time() - t0), flush=True)
ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)); res = {}
for mode in MODES:
    xtr = picture(S[~te], mode)
    fes = [Features(64, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
    ctr = enc(xtr); tests = {"clean": enc(picture(S[te], mode))}
    for snr in (20, 10, 5):
        tests[f"{snr}dB"] = enc(picture(noisy[snr], mode))
    accs = {k: [] for k in tests}
    for seed in (1, 2, 3):
        m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
            m.stage(ctr[sel], ytr[sel])
        for k, c in tests.items():
            accs[k].append(float((m.predict(c) == yte).mean()))
    res[mode] = {k: round(float(np.mean(v)), 4) for k, v in accs.items()}
    print(mode, res[mode], "%.0fs" % (time.time() - t0), flush=True)
json.dump({"label": "SIMULATED (integer cochlea, exact integer chip model, 3 seeds; white noise, fixed seed)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "noisy_align.json"), "w"), indent=1)
