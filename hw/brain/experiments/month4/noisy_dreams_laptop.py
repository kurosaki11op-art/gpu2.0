"""Noisy dreams (21 Oct 2026): the chip learns from CLEAN clips only, but each night dream has a few of its bits dropped and a few spurious bits added (imperfect replay), so the table tolerates noise without storing noisy clips. SIMULATED.
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
from cortex_int import _practise, _count, _xs
from cortex_slow import CortexSlow, _follow
try:
    from numba import njit
except ImportError:
    def njit(*a, **k): return (lambda f: f) if not (a and callable(a[0])) else a[0]

@njit(cache=True)
def _dream_noisy(on, n, c, rng, out, drop, add):
    """cortex_int._dream, then: drop each active bit with probability 2^-drop (0 = none), then add (len >> add) random bits (0 = none). xorshift draws only."""
    nb = on.shape[1]; nc = n[c]
    if nc == 0: return 0
    L = 0
    while (1 << L) <= nc: L += 1
    mask = np.uint32((1 << L) - 1); k = 0
    for b in range(nb):
        lane = b % 32
        while True:
            rng[lane] = _xs(rng[lane]); r = rng[lane] & mask
            if r < nc: break
        if r < on[c, b]:
            keep = True
            if drop > 0:
                rng[lane] = _xs(rng[lane])
                if (rng[lane] & np.uint32((1 << drop) - 1)) == 0: keep = False
            if keep:
                out[k] = b; k += 1
    if add > 0:
        extra = k >> add
        for j in range(extra):
            rng[j % 32] = _xs(rng[j % 32]); out[k] = rng[j % 32] % nb; k += 1
    return k

@njit(cache=True)
def _stage_nd(W, S, on, n, rng, known, acts, nacts, ys, new_cls, old_cls, ndream, night, margin, cmax, top, daydream, night_stop, stats, ch, K, FR, RND, tick0, drop, add):
    """cortex_slow._stage_slow with noisy night dreams (day and daydreams stay clean)."""
    buf = np.zeros(on.shape[1] + on.shape[1] // 2 + 8, np.int32)
    for c in new_cls: known[c] = True
    nreal = len(ys); total_d = ndream * len(old_cls); done_d = 0; rr = 0; writes = 0; tick = tick0
    from_dream = 0
    for i in range(nreal):
        _count(on, n, acts[i], nacts[i], ys[i], top)
        writes += _practise(W, acts[i], nacts[i], ys[i], known, margin, cmax)
        for d in range(daydream):
            k = _dream_noisy(on, n, ys[i], rng, buf, 0, 0)
            writes += _practise(W, buf, k, ys[i], known, margin, cmax)
        due = (total_d * (i + 1)) // nreal
        while done_d < due:
            c = old_cls[rr % len(old_cls)]; rr += 1
            k = _dream_noisy(on, n, c, rng, buf, 0, 0)
            writes += _practise(W, buf, k, c, known, margin, cmax); done_d += 1
        tick += 1
        if tick % ch == 0: _follow(S, W, K, FR, RND)
    if len(old_cls) > 0:
        kn = np.where(known)[0]; blockw = 0; stop = False
        for p in range(night):
            for j in range(ndream * len(kn)):
                c = kn[j % len(kn)]
                k = _dream_noisy(on, n, c, rng, buf, drop, add)
                w = _practise(W, buf, k, c, known, margin, cmax)
                writes += w; blockw += w; stats[0] += 1; stats[1] += w
                tick += 1
                if tick % ch == 0: _follow(S, W, K, FR, RND)
                if night_stop > 0 and stats[0] % 256 == 0:
                    if blockw > night_stop: stop = True; break
                    blockw = 0
            if stop: break
    return writes, tick

class NoisyDreamChip(CortexSlow):
    def __init__(self, n_bits, drop=0, add=0, **kw):
        super().__init__(n_bits, **kw); self.drop, self.add = drop, add
    def stage(self, code, y):
        new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
        A, na = self.pack(code)
        r, self.tick = _stage_nd(self.W, self.S, self.on, self.n, self.rng, self.known, A, na, y.astype(np.int64), new, old.astype(np.int64), self.ndream, self.night, self.margin,
                                 self.cmax, self.top, self.daydream, self.night_stop, self.stats, self.ch, self.K, self.FR, self.RND, self.tick, self.drop, self.add)
        if len(y) < 2 * self.ch: self.S[:] = self.W.astype(np.int32) << self.FR
        return r

VARIANTS = {"clean_dreams": (0, 0), "drop1/8": (3, 0), "drop1/4": (2, 0), "drop1/8+add1/16": (3, 4), "drop1/4+add1/8": (2, 3)}
ctr = enc(picture(trS["clean"]))
for name, (dr, ad) in VARIANTS.items():
    rp = os.path.join(CACHE, "nd_" + name.replace("/", "_") + ".json")
    if os.path.exists(rp): print("noisy dreams", name, json.load(open(rp)), "(cached)", flush=True); continue
    accs = {k: [] for k in tests}
    for seed in (1, 2, 3):
        m = NoisyDreamChip(ctr.shape[1], drop=dr, add=ad, ch=100, K=5, night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
        for k, c in tests.items(): accs[k].append(float((m.predict(c) == yte).mean()))
    rr = {k: round(float(np.mean(v)), 4) for k, v in accs.items()}; json.dump(rr, open(rp, "w")); print("noisy dreams", name, rr, "%.0fs" % (time.time() - t0), flush=True)
