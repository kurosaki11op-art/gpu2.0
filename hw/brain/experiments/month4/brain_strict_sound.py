"""Brain-strict sound tests (21 Oct 2026). SIMULATED, exact integer chip model, 20 words of the 35-word subset (data/sc_subset), 5 stages of 4 words, speaker-disjoint test (hash mod 5 == 0).
Pictures: integer cochlea -> noise floor (low4x4) -> window alignment -> finer sound grid 3,3,1,1,4,4 (64 detectors, 10 thresholds), slow-table chip (K = 5, ch = 100), learned from CLEAN clips.
Arms (env ARMS):
  peak           shipped alignment: the window starts at the first frame reaching 3/4 of the loudest frame of the clip (needs the whole clip: not causal)
  onset:TH       causal onset trigger: the window starts at the first frame whose loudness (sum of its 28 pixels) reaches TH; only the stream up to that frame is used
  nd:DROP:ADD    peak alignment + noisy night dreams (drop bit with p = 2^-DROP, add len >> ADD random bits)
Reports clean / 20 / 10 / 5 dB accuracy overall, and clean accuracy on the first stage's words (oldest) and the last stage's words (newest). usage: SUBSET_DIR [CACHE_DIR]"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea, cochlea_int
from sound_features import SoundFeatures
from cortex_slow import CortexSlow
from noise_floor import picture as _picture
from noisy_dream_chip import NoisyDreamChip

ROOT = sys.argv[1]; CACHE = sys.argv[2] if len(sys.argv) > 2 else "bs_cache"; SEEDS = int(os.environ.get("SEEDS", 3)); t0 = time.time()
ARMS = os.environ.get("ARMS", "peak,onset:800,onset:1600,nd:3:0,nd:2:0,nd:3:4").split(","); OUT = os.environ.get("OUT", "brain_strict_sound.json")
os.makedirs(CACHE, exist_ok=True)
ALL = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d))); WORDS = [ALL[i] for i in sorted(np.random.RandomState(0).permutation(len(ALL))[:20])]
files, y, spk = [], [], []
for wi, w in enumerate(WORDS):
    for f in sorted(os.listdir(os.path.join(ROOT, w))):
        files.append(os.path.join(ROOT, w, f)); y.append(wi); spk.append(int(f.split("_")[0], 16))
y = np.array(y); te = (np.array(spk) % 5) == 0
X = np.stack([cochlea.read(p) for p in files]).astype(np.int16); print("clips", len(y), "test", int(te.sum()), "%.0fs" % (time.time() - t0), flush=True)


def cached(name, fn):
    p = os.path.join(CACHE, name + ".npy")
    if os.path.exists(p): return np.load(p)
    a = fn(); np.save(p, a); return a


def bank(x, snr, seed):
    xc = x.astype(np.float64)
    if snr is not None:
        g = np.random.RandomState(seed); xc = xc + g.standard_normal(xc.shape) * np.sqrt((xc ** 2).mean(1, keepdims=True) / 10 ** (snr / 10))
    xs = np.clip(np.round(xc), -32768, 32767).astype(np.int16)
    return np.concatenate([cochlea_int._bank(xs[i:i + 500].astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, cochlea.FR, cochlea_int.FB) for i in range(0, len(xs), 500)])


S = {"clean": cached("S_clean", lambda: bank(X, None, 0))}
for snr in (20, 10, 5): S[f"{snr}dB"] = cached(f"S_{snr}", lambda snr=snr: bank(X[te], snr, 12345 + snr))
pic = {"clean": _picture(S["clean"], "low4x4")}
for k in ("20dB", "10dB", "5dB"): pic[k] = _picture(S[k], "low4x4")


def onset_align(P, th, lead=6):
    """causal onset: the window starts at the first frame whose loudness reaches th (compare only); no onset found -> frame 0"""
    P0 = np.asarray(P).reshape(len(P), 28, 28); loud = P0.astype(np.int64).sum(1); hit = loud >= th
    start = np.where(hit.any(1), hit.argmax(1), 0); out = np.zeros_like(P0)
    for i in range(len(P0)):
        sh = lead - start[i]
        if sh >= 0: out[i, :, sh:] = P0[i, :, :28 - sh]
        else: out[i, :, :28 + sh] = P0[i, :, -sh:]
    return out.reshape(len(P), -1)


STAGES = [tuple(range(4 * i, 4 * i + 4)) for i in range(5)]; CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)); ytr, yte = y[~te], y[te]
fcache = {}


def codes(mode):
    if mode in fcache: return fcache[mode]
    al = (lambda P: cochlea_int.align_word(P, 6)) if mode == "peak" else (lambda P, th=int(mode.split(":")[1]): onset_align(P, th))
    ptr = al(pic["clean"][~te]); fes = [SoundFeatures(64, c, 3, 3, 1, 1, 4, 4).fit(ptr[np.isin(ytr, STAGES[0])][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 2000]) for f in fes], 1) for i in range(0, len(x), 2000)])
    out = {"tr": enc(ptr), "clean": enc(al(pic["clean"][te]))}
    for k in ("20dB", "10dB", "5dB"): out[k] = enc(al(pic[k]))
    fcache[mode] = out; return out


res = {}
for arm in ARMS:
    kind = arm.split(":")[0]; C = codes("peak" if kind == "nd" else arm); accs = {k: [] for k in ("clean", "20dB", "10dB", "5dB", "oldest", "newest")}
    for seed in range(1, SEEDS + 1):
        m = NoisyDreamChip(C["tr"].shape[1], drop=int(arm.split(":")[1]), add=int(arm.split(":")[2]), n_cls=20, ch=100, K=5, night_stop=2, daydream=1, seed=seed) if kind == "nd" \
            else CortexSlow(C["tr"].shape[1], n_cls=20, ch=100, K=5, night_stop=2, daydream=1, seed=seed)
        for i, s in enumerate(STAGES):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(C["tr"][sel], ytr[sel])
        for k in ("clean", "20dB", "10dB", "5dB"): accs[k].append(float((m.predict(C[k]) == yte).mean()))
        p = m.predict(C["clean"]); accs["oldest"].append(float((p == yte)[np.isin(yte, STAGES[0])].mean())); accs["newest"].append(float((p == yte)[np.isin(yte, STAGES[-1])].mean()))
    res[arm] = {k: round(float(np.mean(v)), 4) for k, v in accs.items()}; json.dump(res, open(OUT, "w"), indent=1); print(arm, res[arm], "%.0fs" % (time.time() - t0), flush=True)
