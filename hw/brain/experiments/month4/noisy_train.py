"""(Noise-trained variant, 19 Oct 2026: the chip learns from clips with noise at random levels (as if learning in a noisy room) and is tested on clean / 20 / 10 / 5 dB. Rows: clean training (84.4/77.5/67.7/57.0 from noisy_slow_geom), mixed, noisy only.) (Variant for the finer sound grid 3,3,1,1,4,4 (env GEO), slow table only; shipped grid numbers: clean/20/10/5 dB 82.7/75.2/64.4/52.3. 19 Oct 2026. Original variant: today vs slow table K = 5, 5 stages, 19 Oct 2026.) Word alignment in noise (does the loudness-based word start survive noise?). As noisy_sound.py, modes:
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
from sound_features import SoundFeatures
from cortex_int import CortexInt
from cortex_slow import CortexSlow
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from noise_floor import picture as _picture  # noqa  (same picture() as the floor / gate experiments)


def picture(S, mode):
    if mode.endswith("_align"):
        return cochlea_int.align_word(_picture(S, mode[:-6]), 6)
    return _picture(S, mode)
GEO = tuple(int(v) for v in os.environ.get("GEO", "3,3,1,1,4,4").split(","))
D = sys.argv[1]; MODES = ["low4x4_align"]; t0 = time.time()
z = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = z["S"], z["y"], z["te"]
root = os.path.join(D, "speech"); test = set(open(os.path.join(root, "testing_list.txt")).read().split())
# raw test clips, in the same order as the frame sums
Xte = []
for w in cochlea.WORDS:
    for f in sorted(os.listdir(os.path.join(root, w))):
        if f"{w}/{f}" in test:
            Xte.append(cochlea.read(os.path.join(root, w, f)))
Xte = np.stack(Xte); g = np.random.RandomState(12345)
Xtr = []
for w in cochlea.WORDS:
    for f in sorted(os.listdir(os.path.join(root, w))):
        if f"{w}/{f}" not in test:
            Xtr.append(cochlea.read(os.path.join(root, w, f)).astype(np.int16))
Xtr = np.stack(Xtr); gt = np.random.RandomState(777)
def noisy_bank(X, snrs, gen):
    # each clip gets one noise level drawn from snrs (None = clean)
    lv = gen.choice(len(snrs), len(X)); res = []
    for i in range(0, len(X), 500):
        xc = X[i:i + 500].astype(np.float64); l = lv[i:i + 500]
        for j, snr in enumerate(snrs):
            if snr is None: continue
            ix = np.where(l == j)[0]; p = (xc[ix] ** 2).mean(1, keepdims=True); xc[ix] = xc[ix] + gen.standard_normal(xc[ix].shape) * np.sqrt(p / 10 ** (snr / 10))
        xs = np.clip(np.round(xc), -32768, 32767).astype(np.int16)
        res.append(cochlea_int._bank(xs.astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, cochlea.FR, cochlea_int.FB))
    return np.concatenate(res)
TRAINS = {"clean": [None], "mixed (clean/20/10/5)": [None, 20, 10, 5], "noisy only (20/10/5)": [20, 10, 5]}
trS = {k: cached("train_" + k.split()[0], lambda k=k, v=v: noisy_bank(Xtr, v, np.random.RandomState(777 + len(k)))) for k, v in TRAINS.items() if k != "clean"}; trS["clean"] = S[~te]
noisy = {}
CACHE = os.path.join(D, "noisy_cache"); os.makedirs(CACHE, exist_ok=True)
def cached(name, fn):
    p = os.path.join(CACHE, name + ".npy")
    if os.path.exists(p): return np.load(p)
    a = fn(); np.save(p, a); return a
def _test_noise(snr):
    gg = np.random.RandomState(12345 + snr)
    p = (Xte ** 2).mean(1, keepdims=True); n = gg.standard_normal(Xte.shape) * np.sqrt(p / 10 ** (snr / 10))
    xn = np.clip(np.round(Xte + n), -32768, 32767).astype(np.int16)
    return np.concatenate([cochlea_int._bank(xn[i:i + 1000].astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G,
                                             cochlea.FR, cochlea_int.FB) for i in range(0, len(xn), 1000)])
for snr in (20, 10, 5):
    noisy[snr] = cached(f"test_{snr}", lambda snr=snr: _test_noise(snr))
print("noisy frame sums ready %.0fs" % (time.time() - t0), flush=True)
ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)); res = {}
for mode in MODES:
    xtr0 = picture(S[~te], mode)
    fes = [SoundFeatures(64, c, *GEO).fit(xtr0[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
    tests = {"clean": enc(picture(S[te], mode))}
    for snr in (20, 10, 5):
        tests[f"{snr}dB"] = enc(picture(noisy[snr], mode))
    accs = {(n_, k): [] for n_ in TRAINS for k in tests}
    for n_ in TRAINS:
        rp = os.path.join(CACHE, "result_" + n_.split()[0] + ".json")
        if os.path.exists(rp):
            for k_, v_ in json.load(open(rp)).items(): accs[(n_, k_)] = [v_]
            print("trained on", n_, json.load(open(rp)), "(from cache)", flush=True); continue
        ctr = enc(picture(trS[n_], mode))
        for seed in (1, 2, 3):
            m = CortexSlow(ctr.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed)
            for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
                sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
                m.stage(ctr[sel], ytr[sel])
            for k, c in tests.items():
                accs[(n_, k)].append(float((m.predict(c) == yte).mean()))
        rr = {k: round(float(np.mean(accs[(n_, k)])), 4) for k in tests}; json.dump(rr, open(rp, "w"))
        print("trained on", n_, rr, "%.0fs" % (time.time() - t0), flush=True)
    res[mode] = {f'{n_}|{k}': round(float(np.mean(v)), 4) for (n_, k), v in accs.items()}
    print(mode, res[mode], "%.0fs" % (time.time() - t0), flush=True)
json.dump({"label": "SIMULATED (integer cochlea, exact integer chip model, 3 seeds; white noise, fixed seed)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "noisy_train.json"), "w"), indent=1)
