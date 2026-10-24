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
torch.set_num_threads(2)
"""Finding Shirts clearly (24 Oct 2026, MEASURED/SIMULATED, Fashion-MNIST, single view, one seed). Shirt-versus-rest ranking quality at every operating point: precision at fixed recall and average precision (AP).
L: score = table score of Shirt minus the best other class score (adds only). CNN ruler: softmax probability of Shirt. Two CNNs: 3 epochs, and 10 epochs with flip/shift augmentation (the stronger ceiling).
Also: 2-way T-shirt vs Shirt accuracy (among those two classes' images) and 4-way accuracy inside {T-shirt, Pullover, Coat, Shirt}."""
Xi = torch.tensor(xtr.reshape(-1, 1, 28, 28).astype(np.float32) / 255.0); Xt = torch.tensor(xte.reshape(-1, 1, 28, 28).astype(np.float32) / 255.0); Yt = torch.tensor(ytr)
def cnn(epochs, aug):
    torch.manual_seed(0); net = nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Dropout(0.3), nn.Linear(64 * 49, 128), nn.ReLU(), nn.Linear(128, 10))
    opt = torch.optim.Adam(net.parameters(), 2e-3); sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs * (len(Xi) // 128 + 1))
    for ep in range(epochs):
        pm = torch.randperm(len(Xi)); net.train()
        for i in range(0, len(Xi), 128):
            b = pm[i:i + 128]; xb = Xi[b]
            if aug: xb = torch.where(torch.rand(len(b), 1, 1, 1) < 0.5, xb.flip(3), xb); dy, dx = np.random.randint(-2, 3, 2); xb = torch.roll(xb, (int(dy), int(dx)), (2, 3))
            loss = nn.functional.cross_entropy(net(xb), Yt[b]); opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    net.eval()
    with torch.no_grad(): return torch.softmax(torch.cat([net(Xt[i:i + 2000]) for i in range(0, 10000, 2000)]), 1).numpy()
m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel]); sl = (centre @ m.S.astype(np.int32).T).astype(np.float64)
models = {"L (shipped code)": (sl.argmax(1), sl[:, 6] - np.delete(sl, 6, 1).max(1), sl)}
for tag, ep, aug in (("CNN 3 epochs", 3, False), ("CNN 10 epochs + augmentation", 10, True)):
    p = cnn(ep, aug); models[tag] = (p.argmax(1), p[:, 6], p)
def pr(score):
    y = (yte == 6); o = np.argsort(-score); tp = np.cumsum(y[o]); prec = tp / np.arange(1, len(o) + 1); rec = tp / y.sum()
    ap = (prec * y[o]).sum() / y.sum(); out = {}
    for r in (0.5, 0.6, 0.7, 0.8): out[r] = prec[np.searchsorted(rec, r)]
    return ap, out
print("| model | overall | Shirt recall (argmax) | Shirt AP | precision @ recall 50 / 60 / 70 / 80 % | 2-way T-shirt vs Shirt | 4-way cluster accuracy |\n|---|---|---|---|---|---|---|")
for k, (pred, sc, full) in models.items():
    ap, o = pr(sc); a2 = np.isin(yte, (0, 6)); p2 = np.where(full[:, 6] > full[:, 0], 6, 0)[a2]; a4 = np.isin(yte, (0, 2, 4, 6)); p4 = np.array((0, 2, 4, 6))[full[:, (0, 2, 4, 6)].argmax(1)][a4]
    print("| %s | %.4f | %.3f | %.3f | %.2f / %.2f / %.2f / %.2f | %.3f | %.3f |" % (k, (pred == yte).mean(), (pred[yte == 6] == 6).mean(), ap, o[0.5], o[0.6], o[0.7], o[0.8], (p2 == yte[a2]).mean(), (p4 == yte[a4]).mean()), flush=True)
