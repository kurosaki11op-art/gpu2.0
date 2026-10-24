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


import time, torch, torch.nn as nn
torch.set_num_threads(2)
"""Learning curve: accuracy against the number of LABELLED examples per class (24 Oct 2026, SIMULATED/MEASURED on CPU). Every method sees the same labelled examples.
L = learned-detector code (detectors learned WITHOUT labels from 12,000 unlabelled training images, as in all L results) + counting table (slow-table model).
Baselines: 1-nearest-neighbour and nearest-class-mean on the same L code; logistic regression on the L code; a small CNN on raw pixels with flip/shift augmentation (no unlabelled data).
Caveat stated in the note: L and the code baselines use unlabelled images to learn the detectors; the CNN does not."""
Xtr_img = xtr.reshape(-1, 28, 28).astype(np.float32) / 255.0; Xte_img = xte.reshape(-1, 28, 28).astype(np.float32) / 255.0
def L_acc(idx):
    m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(0).permutation(len(idx)); m.stage(ctr[idx][sel], ytr[idx][sel])
    return ((centre @ m.S.astype(np.int32).T).argmax(1) == yte).mean()
def knn_acc(idx):
    A = ctr[idx].astype(np.float32); B = centre.astype(np.float32); sc = B @ A.T / (np.sqrt(A.sum(1))[None, :] + 1e-6); return (ytr[idx][sc.argmax(1)] == yte).mean()
def ncm_acc(idx):
    P = np.stack([ctr[idx][ytr[idx] == c].mean(0) for c in range(10)]).astype(np.float32); sc = centre.astype(np.float32) @ P.T / (np.sqrt((P ** 2).sum(1))[None, :] + 1e-6); return (sc.argmax(1) == yte).mean()
def logreg_acc(idx):
    torch.manual_seed(0); X = torch.tensor(ctr[idx], dtype=torch.float32); Y = torch.tensor(ytr[idx]); m = nn.Linear(X.shape[1], 10); opt = torch.optim.Adam(m.parameters(), 1e-2, weight_decay=1e-3)
    for _ in range(150): loss = nn.functional.cross_entropy(m(X), Y); opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad(): return (m(torch.tensor(centre, dtype=torch.float32)).argmax(1).numpy() == yte).mean()
def cnn_acc(idx):
    torch.manual_seed(0); X = torch.tensor(Xtr_img[idx])[:, None]; Y = torch.tensor(ytr[idx])
    m = nn.Sequential(nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(32 * 49, 64), nn.ReLU(), nn.Linear(64, 10))
    opt = torch.optim.Adam(m.parameters(), 2e-3, weight_decay=1e-4); steps = 300
    for s in range(steps):
        b = torch.randint(0, len(X), (min(64, len(X)),)); xb = X[b]; xb = torch.where(torch.rand(len(b), 1, 1, 1) < 0.5, xb.flip(3), xb); dy, dx = np.random.randint(-2, 3, 2); xb = torch.roll(xb, (int(dy), int(dx)), (2, 3))
        loss = nn.functional.cross_entropy(m(xb), Y[b]); opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad(): return (torch.cat([m(torch.tensor(Xte_img[i:i + 2000])[:, None]).argmax(1) for i in range(0, 10000, 2000)]).numpy() == yte).mean()
def fast_scores(idx, X):                                     # fast brain: episodic prototypes (class mean codes), cosine match
    P = np.stack([ctr[idx][ytr[idx] == c].mean(0) for c in range(10)]).astype(np.float32); return X.astype(np.float32) @ P.T / (np.sqrt((P ** 2).sum(1))[None, :] + 1e-6)
def slow_model(idx, **kw):
    m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1, **kw); sel = np.random.RandomState(0).permutation(len(idx)); m.stage(ctr[idx][sel], ytr[idx][sel]); return m
def L_imprint_acc(idx):
    m = slow_model(idx, imprint=4, imprint_sleep=300); return ((centre @ m.S.astype(np.int32).T).argmax(1) == yte).mean()
def two_brains_switch(idx, K=30):                            # fewer than K examples per class: the fast brain decides; otherwise the slow table (the chip knows the per-class counts)
    n = len(idx) // 10
    if n < K: return ncm_acc(idx)
    return L_acc(idx)
def two_brains_blend(idx):                                   # both brains vote with z-scored scores, the fast brain weighted by 1/(1+n/10) (a shift in hardware)
    n = len(idx) // 10; m = slow_model(idx, imprint=4, imprint_sleep=300); ss = (centre @ m.S.astype(np.int32).T).astype(np.float32); fs = fast_scores(idx, centre)
    z = lambda a: (a - a.mean(1, keepdims=True)) / (a.std(1, keepdims=True) + 1e-6); w = 1.0 / (1.0 + n / 10.0)
    return ((w * z(fs) + (1 - w) * z(ss)).argmax(1) == yte).mean()
methods = {"L counting table": L_acc, "L + IMPRINT + short sleep": L_imprint_acc, "fast brain only (class means)": ncm_acc, "two brains: switch at 30": two_brains_switch, "two brains: blend": two_brains_blend, "small CNN, raw pixels": cnn_acc}
print("| labelled examples per class | " + " | ".join(methods) + " |\n|---|" + "---|" * len(methods), flush=True)
for n in (1, 2, 5, 10, 20, 50, 100, 300):
    res = {k: [] for k in methods}
    for seed in range(4 if n <= 20 else 3):
        r = np.random.RandomState(1000 + seed); idx = np.concatenate([r.choice(np.where(ytr == c)[0], n, replace=False) for c in range(10)])
        for k, f in methods.items(): res[k].append(f(idx))
    print("| %d | " % n + " | ".join("%.1f +- %.1f" % (100 * np.mean(v), 100 * np.std(v)) for v in res.values()) + " |", flush=True)
