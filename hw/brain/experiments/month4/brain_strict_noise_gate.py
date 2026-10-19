"""Noise robustness without paying for it (19 Oct 2026). SIMULATED. 20 words of the 35-word subset, 5 stages of 4 words, speaker-disjoint test (hash mod 5 == 0), slow-table chip (K = 5, ch = 50), finer sound grid, shipped alignment.
Training arms (each stage: the clean clips first, then the noisy copies):
  clean   clean clips only (the shipped way)
  noisy   clean clips, then one noisy copy of every clip (SNR 20 / 10 / 5 dB at random, one copy each), all learned
  gated   clean clips, then the noisy copies, but a noisy copy is learned only if its 3 window starts (lead 5, 6, 7) make the chip name the same class (agreement across time-shifted views)
Test: clean, 20, 10, 5 dB white noise, single view; also first-stage words (oldest) and last-stage words (newest) on clean test clips. usage: SUBSET_DIR [CACHE_DIR]; env SEEDS, NW, ARMS."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea, cochlea_int
from sound_features import SoundFeatures
from cortex_slow import CortexSlow
from noise_floor import picture as _picture
ROOT = sys.argv[1]; CACHE = sys.argv[2] if len(sys.argv) > 2 else "bs_cache"; SEEDS = int(os.environ.get("SEEDS", 3)); NW = int(os.environ.get("NW", 20)); ARMS = os.environ.get("ARMS", "clean,noisy,gated").split(","); t0 = time.time()
os.makedirs(CACHE, exist_ok=True); ALL = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d))); WORDS = [ALL[i] for i in sorted(np.random.RandomState(0).permutation(len(ALL))[:NW])]
files, y, spk = [], [], []
for wi, w in enumerate(WORDS):
    for f in sorted(os.listdir(os.path.join(ROOT, w))): files.append(os.path.join(ROOT, w, f)); y.append(wi); spk.append(int(f.split("_")[0], 16))
y = np.array(y); te = (np.array(spk) % 5) == 0; X = np.stack([cochlea.read(p) for p in files]).astype(np.int16)


def cached(name, fn):
    p = os.path.join(CACHE, name + ".npy")
    if os.path.exists(p): return np.load(p)
    a = fn(); np.save(p, a); return a


def bank(x, snr, seed):
    xc = x.astype(np.float64)
    if snr is not None: g = np.random.RandomState(seed); xc = xc + g.standard_normal(xc.shape) * np.sqrt((xc ** 2).mean(1, keepdims=True) / 10 ** (snr / 10))
    xs = np.clip(np.round(xc), -32768, 32767).astype(np.int16)
    return np.concatenate([cochlea_int._bank(xs[i:i + 500].astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, cochlea.FR, cochlea_int.FB) for i in range(0, len(xs), 500)])


Sc = cached("S_clean", lambda: bank(X, None, 0)); Ste = {s: cached(f"S_{s}", lambda s=s: bank(X[te], s, 12345 + s)) for s in (20, 10, 5)}
Str_noisy = {s: cached(f"Strain_{s}_nw{NW}", lambda s=s: bank(X[~te], s, 777 + s)) for s in (20, 10, 5)}; print("cochlea done %.0fs" % (time.time() - t0), flush=True)
pic = lambda S: _picture(S, "low4x4"); al = lambda P, lead: cochlea_int.align_word(P, lead)
ytr, yte = y[~te], y[te]; STAGES = [tuple(range(NW // 5 * i, NW // 5 * i + NW // 5)) for i in range(5)]; CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
ptr = al(pic(Sc)[~te], 6); fes = [SoundFeatures(64, c, 3, 3, 1, 1, 4, 4).fit(ptr[np.isin(ytr, STAGES[0])][:12000]) for c in CH]
enc = lambda P: np.concatenate([np.concatenate([f.encode(P[i:i + 2000]) for f in fes], 1) for i in range(0, len(P), 2000)])
C_tr = enc(ptr); C_te = enc(al(pic(Sc)[te], 6)); T = {s: enc(al(pic(Ste[s]), 6)) for s in (20, 10, 5)}
rg = np.random.RandomState(9); snr_of = rg.choice([20, 10, 5], len(ytr)); N = {lead: np.zeros_like(C_tr) for lead in (5, 6, 7)}
for s in (20, 10, 5):
    ix = np.where(snr_of == s)[0]; P = pic(Str_noisy[s])[ix]
    for lead in (5, 6, 7): N[lead][ix] = enc(al(P, lead))
print("codes ready", C_tr.shape, "%.0fs" % (time.time() - t0), flush=True); NB = C_tr.shape[1]


def pred(m, c):
    s = c.astype(np.int32) @ m.S.T; s[:, ~m.known] = -(1 << 30); return s.argmax(1)


res = {}
for arm in ARMS:
    acc = {k: [] for k in ("clean", "20dB", "10dB", "5dB", "oldest", "newest", "kept")}
    for seed in range(1, SEEDS + 1):
        m = CortexSlow(NB, n_cls=NW, ch=50, K=5, night_stop=2, daydream=1, seed=seed); kept = tot = 0
        for i, s in enumerate(STAGES):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(C_tr[sel], ytr[sel])
            if arm != "clean":
                ok = np.ones(len(sel), bool)
                if arm == "gated":
                    p0 = pred(m, N[6][sel]); ok = (pred(m, N[5][sel]) == p0) & (pred(m, N[7][sel]) == p0)
                kept += int(ok.sum()); tot += len(ok)
                if ok.sum(): m.stage(N[6][sel][ok], ytr[sel][ok])
        for k, c in (("clean", C_te), ("20dB", T[20]), ("10dB", T[10]), ("5dB", T[5])): acc[k].append(float((pred(m, c) == yte).mean()))
        p = pred(m, C_te); acc["oldest"].append(float((p == yte)[np.isin(yte, STAGES[0])].mean())); acc["newest"].append(float((p == yte)[np.isin(yte, STAGES[-1])].mean())); acc["kept"].append(kept / max(tot, 1))
    res[arm] = {k: round(float(np.mean(v)), 4) for k, v in acc.items()}; print(arm, res[arm], "%.0fs" % (time.time() - t0), flush=True); json.dump(res, open("brain_strict_noise_gate.json", "w"), indent=1)
