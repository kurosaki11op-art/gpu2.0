"""Where do twin-word errors go? (20 Oct 2026) DIAGNOSTIC. Per-word accuracy of the CNN reference (joint training) and of the float ridge readout on the shipped peak code (SPARK's information), and, for the twin words, the share of errors that land on the twin partner vs on other words. usage: SUBSET_DIR CACHE_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, torch, torch.nn as nn
import cochlea_int
from noise_floor import picture as _picture
ROOT = sys.argv[1]; CACHE = sys.argv[2]; NW = int(os.environ.get("NW", 20)); torch.manual_seed(1)
ALL = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d))); WORDS = [ALL[i] for i in sorted(np.random.RandomState(0).permutation(len(ALL))[:NW])]
y, spk = [], []
for wi, w in enumerate(WORDS):
    for f in sorted(os.listdir(os.path.join(ROOT, w))): y.append(wi); spk.append(int(f.split("_")[0], 16))
y = np.array(y); te = (np.array(spk) % 5) == 0; ytr, yte = y[~te], y[te]; print("words", WORDS)
PAIRS = [(a, b) for a, b in (("no", "go"), ("left", "right"), ("up", "off"), ("on", "off"), ("bed", "bird"), ("down", "dog"), ("three", "tree"), ("four", "forward")) if a in WORDS and b in WORDS]
S = np.load(os.path.join(CACHE, "S_clean.npy")); P = cochlea_int.align_word(_picture(S, "low4x4"), 6).reshape(len(S), 1, 28, 28).astype(np.float32); Pn = P / max(1.0, float(np.percentile(P, 99.5)))
Xtr, Ytr_t, Xte = torch.tensor(Pn[~te]), torch.tensor(ytr), torch.tensor(Pn[te])
net = nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(64 * 49, 128), nn.ReLU(), nn.Linear(128, NW)); opt = torch.optim.Adam(net.parameters(), 1e-3)
for _ in range(25):
    p = torch.randperm(len(Xtr))
    for i in range(0, len(Xtr), 32): b = p[i:i + 32]; opt.zero_grad(); nn.functional.cross_entropy(net(Xtr[b]), Ytr_t[b]).backward(); opt.step()
with torch.no_grad(): pc = net(Xte).argmax(1).numpy()
tr = np.concatenate([np.load(os.path.join(CACHE, "ch_peak_nw%d_c%d.npz" % (NW, c)))["tr"] for c in range(10)], 1).astype(np.float32); tt = np.concatenate([np.load(os.path.join(CACHE, "ch_peak_nw%d_c%d.npz" % (NW, c)))["clean"] for c in range(10)], 1).astype(np.float32)
mu = tr.mean(0); A = tr - mu; Kt = A @ A.T; Kte = (tt - mu) @ A.T; Y = np.eye(NW, dtype=np.float32)[ytr]; best = (0, None)
for lam in (30.0, 100.0, 300.0, 1000.0):
    al = np.linalg.solve(Kt + lam * np.eye(len(Kt), dtype=np.float32), Y - Y.mean(0)); pr = (Kte @ al).argmax(1); a = (pr == yte).mean()
    if a > best[0]: best = (a, pr)
pr = best[1]; print("overall: CNN %.3f  SPARK float readout %.3f" % ((pc == yte).mean(), (pr == yte).mean()))
partner = {}
for a, b in PAIRS: partner.setdefault(a, []).append(b); partner.setdefault(b, []).append(a)
print("%-9s %5s | %-22s | %-22s" % ("word", "n", "CNN acc (to partner)", "SPARK acc (to partner)"))
for w in sorted(partner):
    i = WORDS.index(w); m = yte == i; pi = [WORDS.index(q) for q in partner[w]]
    f = lambda p: "%.2f (%.2f)" % ((p[m] == i).mean(), np.isin(p[m], pi).mean())
    print("%-9s %5d | %-22s | %-22s  partner(s) %s" % (w, m.sum(), f(pc), f(pr), ",".join(partner[w])))
tw = [WORDS.index(w) for w in partner]; m = np.isin(yte, tw)
for name, p in (("CNN", pc), ("SPARK", pr)):
    wrong = m & (p != yte); inp = np.array([p[j] in [WORDS.index(q) for q in partner[WORDS[yte[j]]]] for j in np.where(wrong)[0]]); print(name, "twin-word errors %d, to a twin partner %.2f, to another word %.2f" % (wrong.sum(), inp.mean(), 1 - inp.mean()))
for name, p in (("CNN", pc), ("SPARK", pr)): nt = ~m; print(name, "non-twin words accuracy %.3f, twin words %.3f" % ((p[nt] == yte[nt]).mean(), (p[m] == yte[m]).mean()))
