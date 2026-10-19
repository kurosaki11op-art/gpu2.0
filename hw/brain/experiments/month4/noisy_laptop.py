"""Noise-trained learning, self-contained for a laptop (19 Oct 2026). Needs only the extracted Speech Commands v0.02 folder (e.g. D:\\sc_full) and numpy, scipy, numba.
Ten words (cochlea.WORDS), test clips = the clips in the set's testing_list.txt (speaker-disjoint; without that file a speaker-hash split), train = the rest, at most NTR per word (default 300) and NTE per word (default 100).
Same chain as noisy_slow_geom.py / noisy_train.py: integer cochlea -> noise floor (low4x4) -> word alignment -> finer sound grid 3,3,1,1,4,4 (64 detectors, 10 thresholds) -> slow-table chip model, 5 stages of 2 words, 3 seeds.
The chip learns from (a) clean clips, (b) clips with noise at a random level from clean / 20 / 10 / 5 dB, (c) clips with noise at a random level from 20 / 10 / 5 dB; each is tested on clean and on 20 / 10 / 5 dB white noise.
Finished pieces are cached in CACHE_DIR, so after an interruption just run the same command again. usage: python noisy_laptop.py SC_DIR [CACHE_DIR=noisy_cache] [NTR=300] [NTE=100]. SIMULATED."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea, cochlea_int
from sound_features import SoundFeatures
from cortex_slow import CortexSlow
from noise_floor import picture as _picture
SC = sys.argv[1]; CACHE = sys.argv[2] if len(sys.argv) > 2 else "noisy_cache"; NTR = int(sys.argv[3]) if len(sys.argv) > 3 else 300; NTE = int(sys.argv[4]) if len(sys.argv) > 4 else 100
os.makedirs(CACHE, exist_ok=True); t0 = time.time()
def cached(name, fn):
    p = os.path.join(CACHE, name + ".npy")
    if os.path.exists(p): return np.load(p)
    a = fn(); np.save(p, a); return a
def picture(S): return cochlea_int.align_word(_picture(S, "low4x4"), 6)
tl = os.path.join(SC, "testing_list.txt"); test = set(open(tl).read().split()) if os.path.exists(tl) else None
files = {"tr": [], "te": []}; ytr, yte = [], []
for wi, w in enumerate(cochlea.WORDS):
    fs = sorted(f for f in os.listdir(os.path.join(SC, w)) if f.endswith(".wav")); a, b = [], []
    for f in fs:
        is_te = (f"{w}/{f}" in test) if test is not None else (int(f.split("_")[0], 16) % 5 == 0)
        (b if is_te else a).append(f)
    rs = np.random.RandomState(wi); a = [a[i] for i in rs.permutation(len(a))[:NTR]]; b = [b[i] for i in rs.permutation(len(b))[:NTE]]
    files["tr"] += [os.path.join(SC, w, f) for f in a]; ytr += [wi] * len(a); files["te"] += [os.path.join(SC, w, f) for f in b]; yte += [wi] * len(b)
ytr, yte = np.array(ytr), np.array(yte); print("train", len(ytr), "test", len(yte), flush=True)
def load(part): return np.stack([cochlea.read(p) for p in files[part]]).astype(np.int16)
def bank(X, snrs, seed):
    gen = np.random.RandomState(seed); lv = gen.choice(len(snrs), len(X)); out = []
    for i in range(0, len(X), 500):
        xc = X[i:i + 500].astype(np.float64); l = lv[i:i + 500]
        for j, snr in enumerate(snrs):
            if snr is None: continue
            ix = np.where(l == j)[0]; p = (xc[ix] ** 2).mean(1, keepdims=True); xc[ix] = xc[ix] + gen.standard_normal(xc[ix].shape) * np.sqrt(p / 10 ** (snr / 10))
        xs = np.clip(np.round(xc), -32768, 32767).astype(np.int16)
        out.append(cochlea_int._bank(xs.astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, cochlea.FR, cochlea_int.FB))
    return np.concatenate(out)
Xtr, Xte = load("tr"), load("te")
TRAINS = {"clean": [None], "mixed": [None, 20, 10, 5], "noisy_only": [20, 10, 5]}
trS = {k: cached("train_" + k, lambda v=v, k=k: bank(Xtr, v, 777 + len(k))) for k, v in TRAINS.items()}
teS = {"clean": cached("test_clean", lambda: bank(Xte, [None], 1))}
for snr in (20, 10, 5): teS[f"{snr}dB"] = cached(f"test_{snr}", lambda snr=snr: bank(Xte, [snr], 12345 + snr))
print("frame sums ready %.0fs" % (time.time() - t0), flush=True)
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
ptr = picture(trS["clean"]); fes = [SoundFeatures(64, c, 3, 3, 1, 1, 4, 4).fit(ptr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 2000]) for f in fes], 1) for i in range(0, len(x), 2000)])
tests = {k: cached("code_test_" + k, lambda v=v: enc(picture(v))) for k, v in teS.items()}
for n_ in TRAINS:
    rp = os.path.join(CACHE, "result_" + n_ + ".json")
    if os.path.exists(rp): print("trained on", n_, json.load(open(rp)), "(cached)", flush=True); continue
    ctr = enc(picture(trS[n_])); accs = {k: [] for k in tests}
    for seed in (1, 2, 3):
        m = CortexSlow(ctr.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
        for k, c in tests.items(): accs[k].append(float((m.predict(c) == yte).mean()))
    rr = {k: round(float(np.mean(v)), 4) for k, v in accs.items()}; json.dump(rr, open(rp, "w")); print("trained on", n_, rr, "%.0fs" % (time.time() - t0), flush=True)
