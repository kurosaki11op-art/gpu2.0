"""Brain-strict sound tests (21 Oct 2026). SIMULATED, exact integer chip model, 20 words of the 35-word subset (data/sc_subset), 5 stages of 4 words, speaker-disjoint test (hash mod 5 == 0).
Pictures: integer cochlea -> noise floor (low4x4) -> window alignment -> finer sound grid 3,3,1,1,4,4 (64 detectors, 10 thresholds), slow-table chip (K = 5, ch = 100), learned from CLEAN clips.
Arms (env ARMS):
  peak           shipped alignment: the window starts at the first frame reaching 3/4 of the loudest frame of the clip (needs the whole clip: not causal)
  onset:TH       causal onset trigger: the window starts at the first frame whose loudness (sum of its 28 pixels) reaches TH; only the stream up to that frame is used
  onsetla:TH     onset trigger (as onset:TH) plus look again at test: scores summed over the window starting at the onset frame - 1, 0, + 1
  peakla         shipped alignment plus the same look-again views (control for onsetla)
  v2             shipped alignment + a second layer learned on the chip rule over 3 x 3 spot windows (frequency x time), 2 x 2 pooled
  tm:D           shipped alignment + timing cells: two extra channels, rise / fall by more than D since the previous frame (auditory onset / offset cells)
  rel:TH         adaptive causal onset: first frame whose loudness reaches 3 x the running average of earlier frames + TH
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
CFG = dict(margin=int(os.environ.get('MARGIN', 32)), ndream=int(os.environ.get('NDREAM', 6000)), night=int(os.environ.get('NIGHT', 2)))   # chip settings (shipped: margin 32, 6,000 dreams, 2 night passes)
ALL = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d))); NW = int(os.environ.get('NW', 20)); WORDS = [ALL[i] for i in sorted(np.random.RandomState(0).permutation(len(ALL))[:NW])]
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


def rel_align(P, th, lead=6):
    """adaptive onset: loudness is compared with a running average of the earlier frames (b += (L - b) >> 2, shift only); the window starts at the first frame with L >= 3 * b + th (a sudden rise, as the ear's adaptation responds); no onset -> frame 0"""
    P0 = np.asarray(P).reshape(len(P), 28, 28); loud = P0.astype(np.int64).sum(1); start = np.zeros(len(P0), np.int64)
    for i in range(len(P0)):
        b = 0
        for t in range(28):
            if loud[i, t] >= 3 * b + th: start[i] = t; break
            b += (loud[i, t] - b) >> 2
    out = np.zeros_like(P0)
    for i in range(len(P0)):
        sh = lead - start[i]
        if sh >= 0: out[i, :, sh:] = P0[i, :, :28 - sh]
        else: out[i, :, :28 + sh] = P0[i, :, -sh:]
    return out.reshape(len(P), -1)


SW = NW // 5; TWIN = [w for a, b in (("no", "go"), ("left", "right"), ("up", "off"), ("on", "off"), ("bed", "bird"), ("down", "dog"), ("three", "tree"), ("four", "forward")) if a in WORDS and b in WORDS for w in (a, b)]; TWIN_IDX = [WORDS.index(w) for w in TWIN]   # acoustic twins present in the word list
SW = NW // 5; STAGES = [tuple(range(SW * i, SW * i + SW)) for i in range(5)]; CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)); ytr, yte = y[~te], y[te]
fcache = {}


def coincidence(P, delays=range(0, 9)):
    """delay-line coincidence cells (auditory-brainstem style): 28 frequency rows -> 7 bands; a cell (band A, band B, delay d) fires if an event in A is followed by an event in B d frames later, anywhere in the window. Events: onset (level rose by more than a quarter of the loudest pixel) and level (above half of it). Compares, shifts and ANDs only."""
    P = np.asarray(P).reshape(len(P), 28, 28).astype(np.int32); mx = P.reshape(len(P), -1).max(1)[:, None, None]; prev = np.concatenate([P[:, :, :1], P[:, :, :-1]], 2)
    band = lambda E: E.reshape(len(E), 7, 4, 28).any(2); R = band((P - prev) * 4 > mx); L = band(P * 2 > mx); out = []
    for A, B in ((R, R), (R, L), (L, L)):
        for d in delays:
            Bs = np.zeros_like(B); Bs[:, :, :28 - d] = B[:, :, d:]; out.append((A[:, :, None, :] & Bs[:, None, :, :]).any(3).reshape(len(P), -1))
    return np.concatenate(out, 1)


def codes(mode):
    if mode in fcache: return fcache[mode]
    if mode == "coin":                                              # shipped peak code + delay-line coincidence cells
        base = codes("peak"); al = lambda P: cochlea_int.align_word(P, 6); src = {"tr": pic["clean"][~te], "clean": pic["clean"][te], "20dB": pic["20dB"], "10dB": pic["10dB"], "5dB": pic["5dB"]}
        out = {k: np.concatenate([base[k], coincidence(al(src[k])).astype(base[k].dtype)], 1) for k in base}; fcache[mode] = out; return out
    if mode.startswith("onsetla") or mode == "peakla":       # test views with the window starting 1 frame earlier / later (look again)
        al = (lambda P, L=6: cochlea_int.align_word(P, L)) if mode == "peakla" else (lambda P, L=6, th=int(mode.split(":")[1]): onset_align(P, th, L))
        ptr = al(pic["clean"][~te]); fes = [SoundFeatures(64, c, 3, 3, 1, 1, 4, 4).fit(ptr[np.isin(ytr, STAGES[0])][:12000]) for c in CH]
        enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 2000]) for f in fes], 1) for i in range(0, len(x), 2000)])
        out = {"tr": enc(ptr)}
        for k in ("clean", "20dB", "10dB", "5dB"):
            src = pic[k][te] if k == "clean" else pic[k]
            for L in (5, 6, 7): out[k + str(L)] = enc(al(src, L))
        fcache[mode] = out; return out
    al = (lambda P: cochlea_int.align_word(P, 6)) if mode == "peak" or mode.startswith("geom") or mode.startswith("tm") else (lambda P, th=int(mode.split(":")[1]): rel_align(P, th)) if mode.startswith("rel") else (lambda P, th=int(mode.split(":")[1]): onset_align(P, th))
    GEO = tuple(int(v) for v in mode.split(":")[1:]) if mode.startswith("geom") else (3, 3, 1, 1, 4, 4)           # window rows, window columns (time), strides, pooling (rows, columns)
    chs = CH + (("rise", int(mode.split(":")[1])), ("fall", int(mode.split(":")[1]))) if mode.startswith("tm") else CH             # tm:D adds timing cells (rise / fall by more than D since the previous frame) to the code
    ptr = al(pic["clean"][~te]); sets = {"tr": ptr, "clean": al(pic["clean"][te])}
    for k in ("20dB", "10dB", "5dB"): sets[k] = al(pic[k])
    parts = {k: [] for k in sets}                                                                                       # resumable: each channel's codes are saved as soon as they exist (a restart loses at most one channel)
    for ci, c in enumerate(chs):
        key = os.path.join(CACHE, "ch_%s_nw%d_c%d.npz" % (mode.replace(":", "_"), NW, ci))
        if os.path.exists(key):
            z = np.load(key); enc_c = {k: z[k] for k in sets}
        else:
            f = SoundFeatures(64, c, *GEO).fit(ptr[np.isin(ytr, STAGES[0])][:12000])
            enc_c = {k: np.concatenate([f.encode(v[i:i + 2000]) for i in range(0, len(v), 2000)]) for k, v in sets.items()}; np.savez_compressed(key, **enc_c)
        for k in sets: parts[k].append(enc_c[k])
        print("channel", ci, "ready", "%.0fs" % (time.time() - t0), flush=True)
    out = {k: np.concatenate(parts[k], 1) for k in sets}
    fcache[mode] = out; return out


import detector_learn


def _win(code, ch):
    """(B, 16, 576) bool: 3 x 3 windows over the 6 x 6 spots (frequency x time) of channel ch (64 features per spot)"""
    x = code[:, ch * 2304:(ch + 1) * 2304].reshape(len(code), 6, 6, 64); w = np.zeros((len(code), 4, 4, 3, 3, 64), bool)
    for i in range(3):
        for j in range(3): w[:, :, :, i, j] = x[:, i:i + 4, j:j + 4]
    return w.reshape(len(code), 16, 576)


def v2aug(C, MINON=10, F2=64):
    """second layer on the chip's own rule (detector_learn): per channel 64 detectors over 3 x 3 spot windows, 2 x 2 pooled -> 256 bits per channel added to the code"""
    first = np.isin(ytr, STAGES[0]); dets = []
    for ch in range(10):
        sd = detector_learn.StreamDetectors(F2, nb=576, min_on=MINON); sd.learn(_win(C["tr"][first], ch).reshape(-1, 576)); sd.reseed(); dets.append(np.where(sd.cnt >= 0, 1, -1).astype(np.float32))
    def l2(code):
        out = []
        for i in range(0, len(code), 500):
            c = code[i:i + 500]; parts = []
            for ch in range(10):
                w = _win(c, ch); on = (w.sum(2) >= MINON).reshape(len(c), 4, 4); win = (np.where(w, 1, -1).astype(np.float32).reshape(-1, 576) @ dets[ch].T).argmax(1).reshape(len(c), 4, 4)
                z = np.zeros((len(c), 2, 2, F2), bool)
                for di in range(2):
                    for dj in range(2):
                        ww = win[:, di::2, dj::2]; oo = on[:, di::2, dj::2]; bi, ii, jj = np.nonzero(oo); z[bi, ii, jj, ww[bi, ii, jj]] = True
                parts.append(z.reshape(len(c), -1))
            out.append(np.concatenate(parts, 1))
        return np.concatenate(out)
    return {k: np.concatenate([v, l2(v)], 1) for k, v in C.items()}


def run_look(arm):
    """second look for words: table A on the shipped code, table B on a finer code (geometry from FINE, e.g. geom:3:3:1:1:2:2); for the share LOOKP % of test clips whose A margin is lowest the scores of A and B are added"""
    CA, CB = codes("peak"), codes(os.environ.get("FINE", "geom:3:3:1:1:3:3")); accs = {k: {} for k in ("clean", "20dB", "10dB", "5dB")}; share = [float(v) for v in arm.split(":")[1].split("/")]
    sc = lambda m, c: np.where(m.known[None, :], c.astype(np.int32) @ m.S.T.astype(np.int32), -(1 << 28))
    for seed in range(1, SEEDS + 1):
        ms = []
        for C in (CA, CB):
            if os.environ.get("STACK"):                                         # both tables use the tail memory (share 3/16)
                import cortex_rules; os.environ["TMIX"] = "3"; m = cortex_rules.CortexRules(C["tr"].shape[1], rule="tailmem", n_cls=NW, ch=100, K=5, night_stop=2, daydream=1, seed=seed, **CFG)
            else: m = CortexSlow(C["tr"].shape[1], n_cls=NW, ch=100, K=5, night_stop=2, daydream=1, seed=seed, **CFG)
            for i, s in enumerate(STAGES):
                sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(C["tr"][sel], ytr[sel])
            ms.append(m)
        for k in accs:
            sa, sb = sc(ms[0], CA[k]), sc(ms[1], CB[k]); t = np.sort(sa, 1); mg = t[:, -1] - t[:, -2]
            for name, p in [("coarse", sa), ("fine", sb), ("sum", sa + sb)] + [("look%d" % q, np.where((mg < np.percentile(mg, q))[:, None], sa + sb, sa)) for q in share]:
                accs[k].setdefault(name, []).append(float((p.argmax(1) == yte).mean()))
                if k == "clean": accs[k].setdefault(name + " oldest", []).append(float((p.argmax(1) == yte)[np.isin(yte, STAGES[0])].mean())); accs[k].setdefault(name + " newest", []).append(float((p.argmax(1) == yte)[np.isin(yte, STAGES[-1])].mean()))
    return {k + " " + n: round(float(np.mean(v)), 4) for k in accs for n, v in accs[k].items()}


res = {}
for arm in ARMS:
    if arm.startswith("look:"):
        res[arm] = run_look(arm); json.dump(res, open(OUT, "w"), indent=1); print(arm, res[arm], "%.0fs" % (time.time() - t0), flush=True); continue
    kind = arm.split(":")[0]; C = codes("peak" if kind in ("nd", "v2", "hr", "tail") else arm)
    if kind == "v2": C = v2aug(C)
    la = kind in ("onsetla", "peakla"); accs = {k: [] for k in ("clean", "20dB", "10dB", "5dB", "oldest", "newest", "twin", "other")}
    for seed in range(1, SEEDS + 1):
        if kind == "hr":                                                   # hard-example replay: E stored hardest examples per word, replayed in a short night (mix/16 of the replays), then the normal dream night
            import cortex_rules; os.environ["HARD"] = "1"; os.environ["CONS"] = os.environ.get("CONSMODE", "1"); os.environ["REALMIX"] = arm.split(":")[2]
        if kind == "tail":                                                 # surprise-tagged tail memory: the share (n/16) of dreams drawn from the counts of the examples that made the table write
            import cortex_rules; os.environ["TMIX"] = arm.split(":")[1]
        m = cortex_rules.CortexRules(C["tr"].shape[1], rule="tailmem", n_cls=NW, ch=100, K=5, night_stop=2, daydream=1, seed=seed, **CFG) if kind == "tail" \
            else cortex_rules.CortexRules(C["tr"].shape[1], rule="real", par=int(arm.split(":")[1]), n_cls=NW, ch=100, K=5, night_stop=2, daydream=1, seed=seed, **CFG) if kind == "hr" \
            else NoisyDreamChip(C["tr"].shape[1], drop=int(arm.split(":")[1]), add=int(arm.split(":")[2]), n_cls=NW, ch=100, K=5, night_stop=2, daydream=1, seed=seed, **CFG) if kind == "nd" \
            else CortexSlow(C["tr"].shape[1], n_cls=NW, ch=100, K=5, night_stop=2, daydream=1, seed=seed, **CFG)
        for i, s in enumerate(STAGES):
            sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(C["tr"][sel], ytr[sel])
        if la:
            def predict(k):
                sc = sum(C[k + str(L)].astype(np.int32) @ m.S.T for L in (5, 6, 7)); sc[:, ~m.known] = -(1 << 30); return sc.argmax(1)
        else:
            predict = lambda k: m.predict(C[k])
        for k in ("clean", "20dB", "10dB", "5dB"): accs[k].append(float((predict(k) == yte).mean()))
        p = predict("clean"); accs["oldest"].append(float((p == yte)[np.isin(yte, STAGES[0])].mean())); tw = np.isin(yte, TWIN_IDX); accs["twin"].append(float((p == yte)[tw].mean()) if tw.any() else 0.0); accs["other"].append(float((p == yte)[~tw].mean())); accs["newest"].append(float((p == yte)[np.isin(yte, STAGES[-1])].mean()))
    res[arm] = {k: round(float(np.mean(v)), 4) for k, v in accs.items()}; json.dump(res, open(OUT, "w"), indent=1); print(arm, res[arm], "%.0fs" % (time.time() - t0), flush=True)
