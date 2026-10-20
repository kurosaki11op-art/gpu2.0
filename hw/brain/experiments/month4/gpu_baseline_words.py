"""GPU-style reference for the 20-word set (20 Oct 2026). A DIAGNOSTIC ruler, not part of the chip. Same clips, same speaker-disjoint split (speaker hash mod 5 == 0 is test), same 28x28 aligned sound picture the chip sees (cochlea, noise floor, peak alignment), same 5 stages of 4 words as the chip tests.
A small CNN (2 conv + 1 hidden layer, Adam, float32): joint (all words, 25 epochs), naive staged (5 epochs per stage on that stage's words only), staged with a replay buffer of RB real pictures (default 160, about the chip's memory at 784 bytes each; also 1,000).
usage: SUBSET_DIR CACHE_DIR"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, torch, torch.nn as nn
import cochlea, cochlea_int
from noise_floor import picture as _picture
ROOT = sys.argv[1]; CACHE = sys.argv[2]; NW = 20; STAGES = [tuple(range(4 * i, 4 * i + 4)) for i in range(5)]; torch.manual_seed(1)
ALL = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d))); WORDS = [ALL[i] for i in sorted(np.random.RandomState(0).permutation(len(ALL))[:NW])]
y, spk = [], []
for wi, w in enumerate(WORDS):
    for f in sorted(os.listdir(os.path.join(ROOT, w))): y.append(wi); spk.append(int(f.split("_")[0], 16))
y = np.array(y); te = (np.array(spk) % 5) == 0
S = np.load(os.path.join(CACHE, "S_clean.npy")); P = cochlea_int.align_word(_picture(S, "low4x4"), 6).reshape(len(S), 1, 28, 28).astype(np.float32)
P = P / max(1.0, float(np.percentile(P, 99.5)))
Xtr, Ytr, Xte, Yte = torch.tensor(P[~te]), torch.tensor(y[~te]), torch.tensor(P[te]), torch.tensor(y[te]); print("train", len(Ytr), "test", len(Yte), flush=True)


def net(): return nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(64 * 49, 128), nn.ReLU(), nn.Linear(128, NW))


def fit(m, X, Y, epochs):
    opt = torch.optim.Adam(m.parameters(), 1e-3)
    for _ in range(epochs):
        p = torch.randperm(len(X))
        for i in range(0, len(X), 32):
            b = p[i:i + 32]; opt.zero_grad(); nn.functional.cross_entropy(m(X[b]), Y[b]).backward(); opt.step()


TWIN = [w for a, b in (("no", "go"), ("left", "right"), ("up", "off"), ("on", "off"), ("bed", "bird"), ("down", "dog"), ("three", "tree"), ("four", "forward")) if a in WORDS and b in WORDS for w in (a, b)]; TI = torch.tensor(np.isin(y[te], [WORDS.index(w) for w in TWIN]))


def acc(m):
    with torch.no_grad(): p = m(Xte).argmax(1)
    return float((p == Yte).float().mean()), float((p[TI] == Yte[TI]).float().mean())


m = net(); fit(m, Xtr, Ytr, 25); print("20 words joint (overall, twin words)", [round(v, 4) for v in acc(m)], flush=True)
for name, rb in (("naive", 0), ("replay RB=160", 160), ("replay RB=1000", 1000)):
    m = net(); buf = np.zeros(0, np.int64)
    for s in STAGES:
        cur = np.where(np.isin(y[~te], s))[0]; sel = np.concatenate([cur, buf]); fit(m, Xtr[sel], Ytr[sel], 5)
        if rb: old = np.concatenate([buf, cur]); buf = old[np.random.RandomState(7).permutation(len(old))[:rb]]
    print("20 words staged", name, [round(v, 4) for v in acc(m)], flush=True)
