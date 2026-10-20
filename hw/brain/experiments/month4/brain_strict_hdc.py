"""Hyperdimensional temporal binding for words (20 Oct 2026) PROBE, SIMULATED. Each frame's events (28 frequency rows x {rise, level}) are bundled from random item hypervectors (D bits); consecutive frames are bound with a one-step permutation (XOR with the next frame rotated by one bit) so ORDER is coded;
the bound pairs of the whole window are bundled by majority into one D-bit vector (shift-invariant n-gram coding, XOR / rotate / majority only). Float dual-ridge ceiling on: shipped peak code, HDC code alone, both; overall and twin words. usage: SUBSET_DIR CACHE_DIR; env D."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea, cochlea_int
from noise_floor import picture as _picture
ROOT = sys.argv[1]; CACHE = sys.argv[2]; NW = 20; DH = int(os.environ.get("D", 4096))
ALL = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d))); WORDS = [ALL[i] for i in sorted(np.random.RandomState(0).permutation(len(ALL))[:NW])]
files, y, spk = [], [], []
for wi, w in enumerate(WORDS):
    for f in sorted(os.listdir(os.path.join(ROOT, w))): files.append(os.path.join(ROOT, w, f)); y.append(wi); spk.append(int(f.split("_")[0], 16))
y = np.array(y); te = (np.array(spk) % 5) == 0; ytr, yte = y[~te], y[te]
TWIN = [w for a, b in (("no", "go"), ("left", "right"), ("up", "off"), ("on", "off"), ("bed", "bird"), ("down", "dog"), ("three", "tree"), ("four", "forward")) if a in WORDS and b in WORDS for w in (a, b)]; TI = np.isin(yte, [WORDS.index(w) for w in TWIN])
S = np.load(os.path.join(CACHE, "S_clean.npy")); P = cochlea_int.align_word(_picture(S, "low4x4"), 6).reshape(len(S), 28, 28).astype(np.int32); Ytr = np.eye(NW, dtype=np.float32)[ytr]
g = np.random.RandomState(3); ITEM = g.rand(56, DH) < 0.5                                  # item memory: one random hypervector per (row, event type)


def hdc(P):
    mx = P.reshape(len(P), -1).max(1)[:, None, None]; prev = np.concatenate([P[:, :, :1], P[:, :, :-1]], 2); ev = np.concatenate([(P - prev) * 4 > mx, P * 2 > mx], 1)      # (N, 56, 28 frames)
    out = np.zeros((len(P), DH), bool)
    for i0 in range(0, len(P), 200):
        e = ev[i0:i0 + 200].astype(np.float32); cnt = e.sum(1)                                  # active events per frame
        fr = np.einsum("nsf,sd->nfd", e, ITEM.astype(np.float32)) * 2 - cnt[:, :, None]         # bundle: signed vote per bit (frames x D)
        fb = fr > 0; acc = np.zeros((len(e), DH), np.float32)
        for t in range(27):
            bound = fb[:, t] ^ np.roll(fb[:, t + 1], 1, axis=1); acc += np.where((cnt[:, t] > 0) & (cnt[:, t + 1] > 0), 1, 0)[:, None] * (bound * 2 - 1)
        out[i0:i0 + 200] = acc > 0
    return out


def ridge(a, b, lams=(30.0, 100.0, 300.0, 1000.0)):
    a = a.astype(np.float32); b = b.astype(np.float32); mu = a.mean(0); A = a - mu; Kt = A @ A.T; Kte = (b - mu) @ A.T; best = (0, 0)
    for lam in lams:
        al = np.linalg.solve(Kt + lam * np.eye(len(Kt), dtype=np.float32), Ytr - Ytr.mean(0)); p = (Kte @ al).argmax(1); r = (float((p == yte).mean()), float((p[TI] == yte[TI]).mean()))
        if r[0] > best[0]: best = r
    return best


base_tr = np.concatenate([np.load(os.path.join(CACHE, "ch_peak_nw20_c%d.npz" % c))["tr"] for c in range(10)], 1); base_te = np.concatenate([np.load(os.path.join(CACHE, "ch_peak_nw20_c%d.npz" % c))["clean"] for c in range(10)], 1)
h = hdc(P); h_tr, h_te = h[~te], h[te]; print("hdc bits", DH, "mean on", round(float(h.mean()), 3), flush=True)
for name, a, b in (("shipped peak code", base_tr, base_te), ("HDC temporal code alone", h_tr, h_te), ("shipped + HDC", np.concatenate([base_tr, h_tr], 1), np.concatenate([base_te, h_te], 1))):
    r = ridge(a, b); print(name, "overall %.4f  twin words %.4f" % r, flush=True)
