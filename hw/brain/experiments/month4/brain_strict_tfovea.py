"""Temporal fovea for sound (20 Oct 2026) PROBE, SIMULATED. The shipped picture has 28 frames of ~36 ms for the whole second, so a consonant burst at the word's start falls inside one frame. Here the same integer cochlea also runs with 8x finer frames (224 frames, ~4.5 ms); the word's start is found by the shipped alignment on the coarse picture and
a window of 28 fine frames (~125 ms) beginning one coarse frame before it is turned into a second 28x28 picture (same noise floor per resonator, same integer log, same level scale). It is encoded with the same detector rule (10 channels, learned on the first stage's words) and appended to the shipped code.
Float dual-ridge ceiling on: shipped peak code, fine window alone, both; overall and twin words (20 words, speaker-disjoint). usage: SUBSET_DIR CACHE_DIR"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea, cochlea_int
from sound_features import SoundFeatures
from noise_floor import picture as _picture
ROOT = sys.argv[1]; CACHE = sys.argv[2]; NW = 20; t0 = time.time(); FF = int(os.environ.get('FF', 224)); CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
ALL = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d))); WORDS = [ALL[i] for i in sorted(np.random.RandomState(0).permutation(len(ALL))[:NW])]
files, y, spk = [], [], []
for wi, w in enumerate(WORDS):
    for f in sorted(os.listdir(os.path.join(ROOT, w))): files.append(os.path.join(ROOT, w, f)); y.append(wi); spk.append(int(f.split("_")[0], 16))
y = np.array(y); te = (np.array(spk) % 5) == 0; ytr, yte = y[~te], y[te]; SW = NW // 5; STAGES = [tuple(range(SW * i, SW * i + SW)) for i in range(5)]
TWIN = [w for a, b in (("no", "go"), ("left", "right"), ("up", "off"), ("on", "off"), ("bed", "bird"), ("down", "dog"), ("three", "tree"), ("four", "forward")) if a in WORDS and b in WORDS for w in (a, b)]; TI = np.isin(yte, [WORDS.index(w) for w in TWIN])
Sc = np.load(os.path.join(CACHE, "S_clean.npy")); pc = _picture(Sc, "low4x4").reshape(len(Sc), 28, 28)
pf = os.path.join(CACHE, "Sfine_clean.npy" if FF == 224 else "Sfine%d_clean.npy" % FF)
if os.path.exists(pf): Sf = np.load(pf)
else:
    X = np.stack([cochlea.read(p) for p in files]).astype(np.int16)
    Sf = np.concatenate([cochlea_int._bank(X[i:i + 500].astype(np.int64), cochlea_int.A1, cochlea_int.A2, cochlea_int.G, FF, cochlea_int.FB) for i in range(0, len(X), 500)]); np.save(pf, Sf)
print("fine frame sums", Sf.shape, "%.0fs" % (time.time() - t0), flush=True)
# the shipped alignment's start frame (coarse), then the fine window
loud = pc.astype(np.int64).sum(1); start = np.argmax(loud >= (loud.max(1, keepdims=True) * 3 >> 2), 1); k = FF // 28
a0 = np.clip((start - 1) * k, 0, FF - 28); win = np.stack([Sf[i, :, a0[i]:a0[i] + 28] for i in range(len(Sf))])               # (N, 28 resonators, 28 fine frames)
fl = (np.sort(Sc.astype(np.int64), 2)[:, :, :4].sum(2, keepdims=True) >> 2) // k                                           # the clip's noise floor per resonator, per fine frame
v = np.maximum(win.astype(np.int64) - fl, 1) << 3                                                                           # x8: a fine frame is 1/8 of a coarse frame, same level scale as the coarse picture
e = np.floor(np.log2(v)).astype(np.int64); lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3)
topc = np.floor(np.log2(np.maximum(Sc.astype(np.int64) - (np.sort(Sc.astype(np.int64), 2)[:, :, :4].sum(2, keepdims=True) >> 2), 1))).astype(np.int64); top = (lambda s: (4 * np.floor(np.log2(np.maximum(s, 1))).astype(np.int64)).reshape(len(s), -1).max(1))(np.maximum(Sc.astype(np.int64) - (np.sort(Sc.astype(np.int64), 2)[:, :, :4].sum(2, keepdims=True) >> 2), 1))[:, None, None]
pic_f = np.clip(255 - (np.maximum(top, lg.reshape(len(lg), -1).max(1)[:, None, None]) - lg) * 8, 0, 255).reshape(len(lg), 784).astype(np.uint8)
pic_c = cochlea_int.align_word(pc.reshape(len(pc), 784), 6)
Ytr = np.eye(NW, dtype=np.float32)[ytr]


def encode(pic):
    first = np.isin(ytr, STAGES[0]); parts_tr, parts_te = [], []
    for c in CH:
        f = SoundFeatures(64, c, 3, 3, 1, 1, 4, 4).fit(pic[~te][first][:12000]); parts_tr.append(np.concatenate([f.encode(pic[~te][i:i + 2000]) for i in range(0, (~te).sum(), 2000)])); parts_te.append(f.encode(pic[te]))
    return np.concatenate(parts_tr, 1), np.concatenate(parts_te, 1)


def ridge(a, b, lams=(30.0, 100.0, 300.0, 1000.0)):
    a = a.astype(np.float32); b = b.astype(np.float32); mu = a.mean(0); A = a - mu; Kt = A @ A.T; Kte = (b - mu) @ A.T; best = (0, 0)
    for lam in lams:
        al = np.linalg.solve(Kt + lam * np.eye(len(Kt), dtype=np.float32), Ytr - Ytr.mean(0)); p = (Kte @ al).argmax(1); r = (float((p == yte).mean()), float((p[TI] == yte[TI]).mean()))
        if r[0] > best[0]: best = r
    return best


base_tr = np.concatenate([np.load(os.path.join(CACHE, "ch_peak_nw20_c%d.npz" % c))["tr"] for c in range(10)], 1); base_te = np.concatenate([np.load(os.path.join(CACHE, "ch_peak_nw20_c%d.npz" % c))["clean"] for c in range(10)], 1)
f_tr, f_te = encode(pic_f); print("fine code", f_tr.shape, "%.0fs" % (time.time() - t0), flush=True)
for name, a, b in (("shipped peak code", base_tr, base_te), ("fine onset window alone", f_tr, f_te), ("shipped + fine onset window", np.concatenate([base_tr, f_tr], 1), np.concatenate([base_te, f_te], 1))):
    r = ridge(a, b); print(name, "overall %.4f  twin words %.4f" % r, flush=True)
