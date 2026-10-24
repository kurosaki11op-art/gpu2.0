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

def proto(idx, X):
    P = np.stack([ctr[idx][ytr[idx] == c].mean(0) for c in range(10)]).astype(np.float32); return X.astype(np.float32) @ P.T / (np.sqrt((P ** 2).sum(1))[None, :] + 1e-6)
def knn_scores(idx, X):                                       # exemplar brain: best match per class among the stored examples (cosine)
    A = ctr[idx].astype(np.float32); A = A / (np.sqrt(A.sum(1, keepdims=True)) + 1e-6); sc = X.astype(np.float32) @ A.T; out = np.full((len(X), 10), -1e9, np.float32)
    for c in range(10): out[:, c] = sc[:, ytr[idx] == c].max(1)
    return out
def table_scores(idx, imprint=True):
    m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1, **({"imprint": 4, "imprint_sleep": 300} if imprint else {})); sel = np.random.RandomState(0).permutation(len(idx)); m.stage(ctr[idx][sel], ytr[idx][sel])
    return (centre @ m.S.astype(np.int32).T).astype(np.float32)
z = lambda a: (a - a.mean(1, keepdims=True)) / (a.std(1, keepdims=True) + 1e-6)
def margin(a): t = np.sort(z(a), 1)[:, -2:]; return t[:, 1] - t[:, 0]
acc = lambda sc: (sc.argmax(1) == yte).mean()
def m_proto(idx): return acc(proto(idx, centre))
def m_knn(idx): return acc(knn_scores(idx, centre))
def m_table(idx): return acc(table_scores(idx, imprint=False))
def m_switch(K):
    return lambda idx: m_proto(idx) if len(idx) // 10 < K else m_table(idx)
def m_margin(idx):                                            # each brain reports a z-scored margin; the more sure brain decides (compares only)
    fs = proto(idx, centre); ks = knn_scores(idx, centre); ts = table_scores(idx, imprint=False)
    pick_t = margin(ts) > np.maximum(margin(fs), margin(ks)); fast = np.where(margin(ks)[:, None] > margin(fs)[:, None], ks, fs)
    out = np.where(pick_t, ts.argmax(1), fast.argmax(1)); return (out == yte).mean()
def m_sum(idx):                                               # z-scored sum of the three brains
    return acc(z(proto(idx, centre)) + z(knn_scores(idx, centre)) + z(table_scores(idx, imprint=False)))

import torch.nn as nn
torch.set_num_threads(2)
Ximg_tr = xtr.reshape(-1, 1, 28, 28).astype(np.float32) / 255.0; Ximg_te = xte.reshape(-1, 1, 28, 28).astype(np.float32) / 255.0
# ---- (1) consolidation: sleep. The fast brain's class means generate dream codes (independent Bernoulli bits at the class mean probability); the slow table learns from the real examples plus the dreams.
def table_consolidated(idx, K=200, seed=0):
    r = np.random.RandomState(seed); P = np.stack([ctr[idx][ytr[idx] == c].mean(0) for c in range(10)])
    dream = np.concatenate([(r.rand(K, ctr.shape[1]) < P[c]).astype(ctr.dtype) for c in range(10)]); dy = np.repeat(np.arange(10), K)
    code = np.concatenate([ctr[idx], dream]); y = np.concatenate([ytr[idx], dy]); sel = r.permutation(len(y))
    m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); m.stage(code[sel], y[sel]); return (centre @ m.S.astype(np.int32).T).astype(np.float32)
def m_consol(idx): return acc(table_consolidated(idx))
def m_consol_sum(idx): return acc(z(proto(idx, centre)) + z(knn_scores(idx, centre)) + z(table_consolidated(idx)))
# ---- (2) validated arbitration: choose the rule by 2-fold cross-validation INSIDE the labelled examples (no test data), then use it on all of them
RULES = ("fast", "sum3", "table")
def scores_for(idx, X_override=None):
    return {"fast": z(proto(idx, centre)) , "knn": z(knn_scores(idx, centre)), "table": z(table_consolidated(idx))}
def cv_pick(idx):
    n = len(idx) // 10
    if n < 4: return "fast"
    r = np.random.RandomState(5); score = {k: 0.0 for k in RULES}
    for fold in range(2):
        tr_i, va_i = [], []
        for c in range(10):
            ii = idx[ytr[idx] == c]; ii = r.permutation(ii); h = len(ii) // 2; (tr_i if fold == 0 else va_i).extend(ii[:h]); (va_i if fold == 0 else tr_i).extend(ii[h:])
        tr_i, va_i = np.array(tr_i), np.array(va_i)
        P = np.stack([ctr[tr_i][ytr[tr_i] == c].mean(0) for c in range(10)]).astype(np.float32); Xv = ctr[va_i].astype(np.float32)
        fs = z(Xv @ P.T / (np.sqrt((P ** 2).sum(1))[None, :] + 1e-6))
        A = ctr[tr_i].astype(np.float32); A = A / (np.sqrt(A.sum(1, keepdims=True)) + 1e-6); sc = Xv @ A.T; ks = np.full((len(va_i), 10), -1e9, np.float32)
        for c in range(10): ks[:, c] = sc[:, ytr[tr_i] == c].max(1)
        m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(0).permutation(len(tr_i)); m.stage(ctr[tr_i][sel], ytr[tr_i][sel]); ts = z((Xv.astype(np.int32) @ m.S.astype(np.int32).T).astype(np.float32))
        yv = ytr[va_i]; score["fast"] += (fs.argmax(1) == yv).mean(); score["sum3"] += ((fs + z(ks) + ts).argmax(1) == yv).mean(); score["table"] += (ts.argmax(1) == yv).mean()
    return max(score, key=score.get)
def m_auto(idx):
    pick = cv_pick(idx); s = scores_for(idx)
    sc = {"fast": s["fast"], "sum3": s["fast"] + s["knn"] + s["table"], "table": s["table"]}[pick]; return acc(sc)
# ---- (4) CNN with self-supervised pretraining: a convolutional autoencoder learns from 12,000 UNLABELLED images; its encoder is frozen and a linear head is trained on the few labels
enc_net = None
def get_encoder():
    global enc_net
    if enc_net is not None: return enc_net
    torch.manual_seed(0); enc = nn.Sequential(nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU())
    dec = nn.Sequential(nn.ConvTranspose2d(64, 32, 2, stride=2), nn.ReLU(), nn.ConvTranspose2d(32, 16, 2, stride=2), nn.ReLU(), nn.Conv2d(16, 1, 3, padding=1), nn.Sigmoid())
    r0 = np.random.RandomState(7); U = torch.tensor(Ximg_tr[r0.choice(len(xtr), 12000, replace=False)]); opt = torch.optim.Adam(list(enc.parameters()) + list(dec.parameters()), 2e-3)
    for ep in range(12):
        perm = torch.randperm(len(U))
        for i in range(0, len(U), 128): b = U[perm[i:i + 128]]; loss = nn.functional.mse_loss(dec(enc(b)), b); opt.zero_grad(); loss.backward(); opt.step()
    enc_net = enc; return enc
def m_cnn_ssl(idx):
    enc = get_encoder()
    with torch.no_grad(): ftr = enc(torch.tensor(Ximg_tr[idx])).flatten(1); fte = torch.cat([enc(torch.tensor(Ximg_te[i:i + 2000])).flatten(1) for i in range(0, 10000, 2000)])
    mu, sd = ftr.mean(0), ftr.std(0) + 1e-3; ftr, fte = (ftr - mu) / sd, (fte - mu) / sd; Y = torch.tensor(ytr[idx]); torch.manual_seed(0)
    head = nn.Linear(ftr.shape[1], 10); opt = torch.optim.Adam(head.parameters(), 1e-2, weight_decay=1e-2)
    for _ in range(200): loss = nn.functional.cross_entropy(head(ftr), Y); opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad(): return (head(fte).argmax(1).numpy() == yte).mean()
methods = {"fast: class means": m_proto, "slow table": m_table, "slow table + sleep (dreams from fast brain)": m_consol, "sum of 3 (table with sleep)": m_consol_sum, "AUTO (rule chosen by 2-fold CV)": m_auto, "CNN, self-supervised encoder + linear head": m_cnn_ssl}
print("| labelled examples per class | " + " | ".join(methods) + " |\n|---|" + "---|" * len(methods), flush=True)
for n in (1, 2, 5, 10, 20, 50, 100, 300):
    res = {k: [] for k in methods}
    for seed in range(3):
        r = np.random.RandomState(1000 + seed); idx = np.concatenate([r.choice(np.where(ytr == c)[0], n, replace=False) for c in range(10)])
        for k, f in methods.items(): res[k].append(f(idx))
    print("| %d | " % n + " | ".join("%.1f +- %.1f" % (100 * np.mean(v), 100 * np.std(v)) for v in res.values()) + " |", flush=True)
