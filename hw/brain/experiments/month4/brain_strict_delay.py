"""Delay-line coincidence probe for words (20 Oct 2026) DIAGNOSTIC, SIMULATED. Auditory-brainstem-style coincidence cells: a cell fires if an event in frequency band A is followed by an event in band B after delay d (binary AND of two delayed lines, OR over time, so it does not depend on where in the window the word sits).
Events: onset events (level rose by more than a quarter of the clip's loudest pixel since the previous frame) and level events (pixel above half of the loudest). 7 bands x 7 bands x delays 0..8 for each pair of event types. Float dual-ridge ceiling on: shipped peak code, coincidence code alone, both.
Reports overall accuracy over the 20 words and on the acoustic twin words. usage: SUBSET_DIR CACHE_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea, cochlea_int
from noise_floor import picture as _picture
ROOT = sys.argv[1]; CACHE = sys.argv[2]; NW = 20
ALL = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d))); WORDS = [ALL[i] for i in sorted(np.random.RandomState(0).permutation(len(ALL))[:NW])]
files, y, spk = [], [], []
for wi, w in enumerate(WORDS):
    for f in sorted(os.listdir(os.path.join(ROOT, w))): files.append(os.path.join(ROOT, w, f)); y.append(wi); spk.append(int(f.split("_")[0], 16))
y = np.array(y); te = (np.array(spk) % 5) == 0; ytr, yte = y[~te], y[te]
TWIN = [w for a, b in (("no", "go"), ("left", "right"), ("up", "off"), ("on", "off"), ("bed", "bird"), ("down", "dog"), ("three", "tree"), ("four", "forward")) if a in WORDS and b in WORDS for w in (a, b)]; TI = np.isin(yte, [WORDS.index(w) for w in TWIN])
S = np.load(os.path.join(CACHE, "S_clean.npy")); P = cochlea_int.align_word(_picture(S, "low4x4"), 6).reshape(len(S), 28, 28).astype(np.int32)
Ytr = np.eye(NW, dtype=np.float32)[ytr]


def events(P):
    mx = P.reshape(len(P), -1).max(1)[:, None, None]; prev = np.concatenate([P[:, :, :1], P[:, :, :-1]], 2)
    rise = (P - prev) * 4 > mx; level = P * 2 > mx                      # compares and shifts only
    band = lambda E: E.reshape(len(E), 7, 4, 28).any(2)               # 28 frequency rows -> 7 bands
    return band(rise), band(level)


def coincidence(P, delays=range(0, 9)):
    R, L = events(P); out = []
    for A, B in ((R, R), (R, L), (L, L)):
        for d in delays:
            Bs = np.zeros_like(B); Bs[:, :, :28 - d] = B[:, :, d:]
            out.append((A[:, :, None, :] & Bs[:, None, :, :]).any(3).reshape(len(P), -1))       # (image, band A, band B): any time t with A[t] and B[t+d]
    return np.concatenate(out, 1)


def ridge(a, b, lams=(30.0, 100.0, 300.0, 1000.0)):
    a = a.astype(np.float32); b = b.astype(np.float32); mu = a.mean(0); A = a - mu; Kt = A @ A.T; Kte = (b - mu) @ A.T; best = (0, 0)
    for lam in lams:
        al = np.linalg.solve(Kt + lam * np.eye(len(Kt), dtype=np.float32), Ytr - Ytr.mean(0)); p = (Kte @ al).argmax(1); r = (float((p == yte).mean()), float((p[TI] == yte[TI]).mean()))
        if r[0] > best[0]: best = r
    return best


base_tr = np.concatenate([np.load(os.path.join(CACHE, "ch_peak_nw20_c%d.npz" % c))["tr"] for c in range(10)], 1); base_te = np.concatenate([np.load(os.path.join(CACHE, "ch_peak_nw20_c%d.npz" % c))["clean"] for c in range(10)], 1)
co = coincidence(P); co_tr, co_te = co[~te], co[te]; print("coincidence bits", co.shape[1], "mean on", round(float(co.mean()), 3), flush=True)
for name, a, b in (("shipped peak code", base_tr, base_te), ("coincidence code alone", co_tr, co_te), ("shipped + coincidence", np.concatenate([base_tr, co_tr], 1), np.concatenate([base_te, co_te], 1))):
    r = ridge(a, b); print(name, "overall %.4f  twin words %.4f" % r, flush=True)
