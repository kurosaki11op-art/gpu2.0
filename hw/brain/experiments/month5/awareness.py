"""(env SLOW=1: CortexSlow, slow table, 18 Oct 2026; env STRIDE1=1: images with detectors at stride 1 and pool 4, 19 Oct 2026.) Final numbers with every adopted option together (16 Oct 2026): margin 32 (default now), word alignment lead 6 for
sound, LOOK AGAIN at test time (images: the picture + 4 one-pixel shifts with the centre counted twice; sound: the word
aligned at start frames 5, 6, 6, 7), IMPRINT + short sleep irrelevant here (no few-shot). Exact integer chip model, 5
seeds, all at once and 5 stages, plus the single-view (no LOOK AGAIN) numbers. usage: DATA_DIR DS"""
import json, os, sys
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
from cortex_slow import CortexSlow
SLOW = True
S1 = True      # images: detectors at stride 1, pool 4 (same 4,608-bit code, finer winner grid)
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    import cochlea_int
    from feature_layer import Features
    f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]
    ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
    v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
    lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
    P0 = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8)
    xtr = cochlea_int.align_word(P0[~te], 6)
    CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
    fes = [Features(64, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)])
    ctr = enc(xtr); views = {L: enc(cochlea_int.align_word(P0[te], L)).astype(np.int32) for L in (5, 6, 7)}
    centre, extra = views[6], [views[5], views[6], views[7]]          # views 5, 6, 6, 7 = centre + [5, 6, 7]
else:
    from feature_layer import Features
    xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    
    CH = (50, 150, ("on", 8), ("off", 8))
    if S1:
        import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
    fes = [Features(32, thr=c, pool=4 if S1 else 2).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)])
    X = xte.reshape(len(xte), 28, 28)

    def shifted(dy, dx):
        out = np.zeros_like(X); ys, yd = (slice(0, 28 - dy), slice(dy, 28)) if dy >= 0 else (slice(-dy, 28), slice(0, 28 + dy))
        xs, xd = (slice(0, 28 - dx), slice(dx, 28)) if dx >= 0 else (slice(-dx, 28), slice(0, 28 + dx))
        out[:, yd, xd] = X[:, ys, xs]; return enc(out.reshape(len(X), -1)).astype(np.int32)

    if S1:
        ctr = enc(xtr)
    centre = enc(xte).astype(np.int32); extra = [shifted(-1, 0), shifted(1, 0), shifted(0, -1), shifted(0, 1)]


import torch, torch.nn as nn
torch.set_num_threads(3)
"""Awareness test (24 Oct 2026, SIMULATED/MEASURED on CPU, Fashion-MNIST). The CNN is a ruler only, never part of the chip. L = slow-table model on the learned-detector code (single view); confidence = margin between the two best table scores (a sparse lookup score).
(a) Selective classification: answer only the images the model is most sure of; accuracy at 100/90/70/50 percent coverage.
(b) Novel-class detection: train on 9 classes, test on all; AUROC of confidence for telling images of the unseen class from images of the seen classes (0.5 chance, 1 perfect)."""
Ximg_tr = torch.tensor(xtr.reshape(-1, 1, 28, 28).astype(np.float32) / 255.0); Ximg_te = torch.tensor(xte.reshape(-1, 1, 28, 28).astype(np.float32) / 255.0)
def make_cnn(): return nn.Sequential(nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(32 * 49, 64), nn.ReLU(), nn.Linear(64, 10))
def train_cnn(idx, epochs=3):
    torch.manual_seed(0); m = make_cnn(); opt = torch.optim.Adam(m.parameters(), 2e-3); Y = torch.tensor(ytr[idx]); X = Ximg_tr[idx]
    for ep in range(epochs):
        pm = torch.randperm(len(X))
        for i in range(0, len(X), 128): b = pm[i:i + 128]; loss = nn.functional.cross_entropy(m(X[b]), Y[b]); opt.zero_grad(); loss.backward(); opt.step()
    return m
def cnn_out(m):
    with torch.no_grad(): lg = torch.cat([m(Ximg_te[i:i + 2000]) for i in range(0, 10000, 2000)])
    p = torch.softmax(lg, 1); return p.argmax(1).numpy(), p.max(1).values.numpy()
def L_out(idx):
    m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(len(idx)); m.stage(ctr[idx][sel], ytr[idx][sel])
    sc = (centre @ m.S.astype(np.int32).T).astype(np.float64); t = np.sort(sc, 1)[:, -2:]; return sc.argmax(1), (t[:, 1] - t[:, 0])
def auroc(pos, neg):
    allv = np.concatenate([pos, neg]); rk = allv.argsort().argsort() + 1; n1, n0 = len(pos), len(neg); return 1 - (rk[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
def risk_cov(pred, conf):
    o = np.argsort(-conf); ok = (pred[o] == yte[o]); return {c: 100 * ok[:int(len(ok) * c / 100)].mean() for c in (100, 90, 70, 50)}
allidx = np.arange(len(ytr)); pl, cl = L_out(allidx); cm = train_cnn(allidx); pc, cc = cnn_out(cm)
print("(a) selective classification, accuracy % when answering only the most confident share of test images")
print("| model | 100 %% | 90 %% | 70 %% | 50 %% |\n|---|---|---|---|---|")
for name, (p, c) in (("L (margin of the two best table scores)", (pl, cl)), ("CNN (max softmax probability)", (pc, cc))):
    r = risk_cov(p, c); print("| %s | %.1f | %.1f | %.1f | %.1f |" % (name, r[100], r[90], r[70], r[50]), flush=True)
print("\n(b) novel-class detection, AUROC; trained on 9 classes, one class never seen\n| unseen class | L | CNN |\n|---|---|---|")
names = ["T-shirt","Trouser","Pullover","Dress","Coat","Sandal","Shirt","Sneaker","Bag","Boot"]; al, ac = [], []
for c in (1, 3, 5, 7, 8, 9):
    base = np.where(ytr != c)[0]; p1, c1 = L_out(base); p2, c2 = cnn_out(train_cnn(base))
    a1 = auroc(c1[yte == c], c1[yte != c]); a2 = auroc(c2[yte == c], c2[yte != c]); al.append(a1); ac.append(a2); print("| %s | %.3f | %.3f |" % (names[c], a1, a2), flush=True)
print("| mean | %.3f | %.3f |" % (np.mean(al), np.mean(ac)))
