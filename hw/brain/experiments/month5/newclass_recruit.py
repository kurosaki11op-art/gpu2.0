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

import feature_layer
if os.environ.get("ALLFIT"):
    F = int(os.environ.get("F", 32)); r0 = np.random.RandomState(7); unl = xtr[r0.choice(len(xtr), 12000, replace=False)]            # unlabeled images of all classes (no labels used)
    fes2 = [Features(F, thr=c, pool=4).fit(unl) for c in CH]
    enc2 = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 200]) for g in fes2], 1) for i in range(0, len(x), 200)])
    ctr, centre = enc2(xtr), enc2(xte).astype(np.int32); print("detectors fitted on 12,000 unlabeled images of all classes, F=%d, code bits %d" % (F, ctr.shape[1]), flush=True)


"""Episodic replay (24 Oct 2026, SIMULATED, Fashion-MNIST): the slow table re-reads the few STORED real examples E times (shuffled each pass) instead of once, as hippocampal replay does in sleep.
Part 1: few examples per class, E = 1, 5, 20, with and without IMPRINT. Part 2: adding one new class to a table trained on the other 9 (new class 6 = Shirt and 9 = Boot), the new examples replayed E times."""
import copy
def table_replay(idx, E, imprint):
    kw = {"imprint": 4, "imprint_sleep": 0} if imprint else {}
    m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1, **kw)
    for e in range(E): sel = np.random.RandomState(e).permutation(len(idx)); m.stage(ctr[idx][sel], ytr[idx][sel])
    return ((centre @ m.S.astype(np.int32).T).argmax(1) == yte).mean()

"""Detector recruitment for a new class (24 Oct 2026, SIMULATED, Fashion-MNIST). Failure studied: a new class with 20 to 100 examples is learned much worse than by a CNN with replay (66 against 91 recall at 100), because the CNN adapts its features while L's detectors are fixed.
Design: when a class arrives, R new detectors per channel are fitted (the same unsupervised Hebbian rule) on the patches of the new class's images only; their bits are APPENDED to the code. The table keeps its old columns (the new bits start at zero for the old classes) and is trained on a small replay buffer
(20 stored old images per class + the new images, E passes). Baselines: same buffer and passes WITHOUT recruitment. Both use exactly the same stored images (the CNN comparison used 20 per old class too)."""
import copy, feature_layer
def encode_with(fes, x): return np.concatenate([np.concatenate([g.encode(x[i:i + 200]) for g in fes], 1) for i in range(0, len(x), 200)])
nb0 = ctr.shape[1]; rows = []
for c in (6, 9):
    base = np.where(ytr != c)[0]; m0 = CortexSlow(nb0, ch=500, K=5, night_stop=2, daydream=1, seed=1, imprint=4, imprint_sleep=300); sel = np.random.RandomState(0).permutation(len(base)); m0.stage(ctr[base][sel], ytr[base][sel])
    for n in (20, 100):
        r = np.random.RandomState(300); new = r.choice(np.where(ytr == c)[0], n, replace=False); buf = np.concatenate([r.choice(np.where(ytr == k)[0], 20, replace=False) for k in range(10) if k != c]); store = np.concatenate([new, buf])
        for R in (0, 8, 16):
            if R:
                fes = [Features(R, thr=t, pool=4, seed=5).fit(xtr[new]) for t in CH]; ex_tr = encode_with(fes, xtr[store]); ex_te = encode_with(fes, xte)
                code_st = np.concatenate([ctr[store], ex_tr], 1); code_te = np.concatenate([centre, ex_te], 1)
            else: code_st, code_te = ctr[store], centre
            nb = code_st.shape[1]; m = CortexSlow(nb, ch=500, K=5, night_stop=2, daydream=1, seed=1, imprint=4, imprint_sleep=300)
            m.W[:, :nb0] = m0.W; m.S[:, :nb0] = m0.S; m.on[:, :nb0] = m0.on; m.n[:] = m0.n; m.known[:] = m0.known; m.tick = m0.tick
            for e in range(10): pm = np.random.RandomState(e).permutation(len(store)); m.stage(code_st[pm], ytr[store][pm])
            p = (code_te @ m.S.astype(np.int32).T).argmax(1); rows.append((c, n, R, 100 * (p[yte == c] == c).mean(), 100 * (p[yte != c] == yte[yte != c]).mean(), nb - nb0)); print("new class %d, n=%d, recruited detectors per channel R=%d (+%d bits): new-class recall %.1f, old-class accuracy (10-way) %.1f" % (c, n, R, nb - nb0, rows[-1][3], rows[-1][4]), flush=True)
print("\n| new examples | R | extra bits | new-class recall % | old-class accuracy % |\n|---|---|---|---|---|")
for n in (20, 100):
    for R in (0, 8, 16): v = np.array([[x[3], x[4], x[5]] for x in rows if x[1] == n and x[2] == R]); print("| %d | %d | %d | %.1f | %.1f |" % (n, R, v[:, 2].mean(), v[:, 0].mean(), v[:, 1].mean()))
