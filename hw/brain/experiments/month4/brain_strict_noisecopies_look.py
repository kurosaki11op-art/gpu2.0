"""(stack: noisy copies + second look) (21 Oct 2026: shipped settings margin 256 / 1,500 dreams / 1 night, ch 100.) Noise robustness without paying for it (19 Oct 2026). SIMULATED. 20 words of the 35-word subset, 5 stages of 4 words, speaker-disjoint test (hash mod 5 == 0), slow-table chip (K = 5, ch = 50), finer sound grid, shipped alignment.
Training arms (each stage: the clean clips first, then the noisy copies):
  clean   clean clips only (the shipped way)
  noisy   clean clips, then one noisy copy of every clip (SNR 20 / 10 / 5 dB at random, one copy each), all learned
  twice   control: clean clips, then the same clean clips again
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
ptr = al(pic(Sc)[~te], 6); first = ptr[np.isin(ytr, STAGES[0])][:12000]
rg = np.random.RandomState(9); snr_of = rg.choice([20, 10, 5], len(ytr))
GEOS = {"coarse": (3, 3, 1, 1, 4, 4), "fine": (3, 3, 1, 1, 3, 3)}; Z = {}
for gname, geo in GEOS.items():
    fes = [SoundFeatures(64, c, *geo).fit(first) for c in CH]
    enc = lambda P: np.concatenate([np.concatenate([f.encode(P[i:i + 2000]) for f in fes], 1) for i in range(0, len(P), 2000)])
    CFN = os.path.join(CACHE, "nl_%s_nw%d.npz" % (gname, NW))
    if os.path.exists(CFN): z = np.load(CFN); Z[gname] = {k: z[k] for k in z.files}; continue
    d = {"tr": enc(ptr), "te": enc(al(pic(Sc)[te], 6))}
    for s_ in (20, 10, 5): d["T%d" % s_] = enc(al(pic(Ste[s_]), 6))
    Nz = np.zeros_like(d["tr"])
    for s_ in (20, 10, 5):
        ix = np.where(snr_of == s_)[0]; Nz[ix] = enc(al(pic(Str_noisy[s_])[ix], 6))
    d["N"] = Nz; np.savez_compressed(CFN, **d); Z[gname] = d
    print(gname, "codes ready", d["tr"].shape, "%.0fs" % (time.time() - t0), flush=True)
sc = lambda m, c: np.where(m.known[None, :], c.astype(np.int32) @ m.S.T.astype(np.int32), -(1 << 28))
SHARES = (20, 40); R = {}
for seed in range(1, SEEDS + 1):
    for arm in ("clean", "noisy"):
        ms = {}
        for gname in GEOS:
            d = Z[gname]; m = CortexSlow(d["tr"].shape[1], n_cls=NW, ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)
            for i, s_ in enumerate(STAGES):
                sel = np.where(np.isin(ytr, s_))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(d["tr"][sel], ytr[sel])
                if arm == "noisy": m.stage(d["N"][sel], ytr[sel])
            ms[gname] = m
        for k, key in (("clean", "te"), ("20dB", "T20"), ("10dB", "T10"), ("5dB", "T5")):
            sa, sb = sc(ms["coarse"], Z["coarse"][key]), sc(ms["fine"], Z["fine"][key]); t = np.sort(sa, 1); mg = t[:, -1] - t[:, -2]
            outs = [("coarse", sa), ("fine", sb), ("sum", sa + sb)] + [("look%d" % q, np.where((mg < np.percentile(mg, q))[:, None], sa + sb, sa)) for q in SHARES]
            for nme, p in outs:
                R.setdefault((arm, nme, k), []).append(float((p.argmax(1) == yte).mean()))
                if k == "clean": R.setdefault((arm, nme, "oldest"), []).append(float((p.argmax(1) == yte)[np.isin(yte, STAGES[0])].mean())); R.setdefault((arm, nme, "newest"), []).append(float((p.argmax(1) == yte)[np.isin(yte, STAGES[-1])].mean()))
    print("seed", seed, "%.0fs" % (time.time() - t0), flush=True)
for arm in ("clean", "noisy"):
    for nme in ("coarse", "fine", "sum", "look20", "look40"):
        print("RESULT", arm, "%-7s" % nme, " ".join("%s %.4f" % (k, np.mean(R[(arm, nme, k)])) for k in ("clean", "20dB", "10dB", "5dB", "oldest", "newest")), flush=True)
json.dump({"|".join(k): float(np.mean(v)) for k, v in R.items()}, open("noisecopies_look_%d.json" % NW, "w"), indent=1)
