"""GPU-style few-shot baseline on the same split (20 Oct; floating point, backprop, a DIAGNOSTIC baseline, not part of the chip): a small CNN is trained with cross-entropy on the OLD words' aligned pictures
(Speech Commands words 0-4, all clips) [variant 'old+fsdd': also on the 10 FSDD digits as extra training classes], the classifier head is dropped, the 64-d embedding is frozen, and the 5 NEW words are enrolled
from k recordings as mean-embedding prototypes (old words: mean embedding of their training clips); a test clip goes to the nearest prototype (cosine). Accuracy over all ten words / new / old, 3 draws.
Shows what a conventional pretrained embedding does with only 5 (or 15) known words. usage: DATA_DIR"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, torch, torch.nn as nn
from sound_align_confirm import align
torch.set_num_threads(3); D = sys.argv[1]
f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int)
fs = np.load(os.path.join(D, "fsdd_framesums_int.npz")); yfs = fs["y"].astype(int)
P = align(S, 6).astype(np.float32) / 255.0; Ptr, Pte = torch.tensor(P[~te]), torch.tensor(P[te]); Pfs = torch.tensor(align(fs["S"], 6).astype(np.float32) / 255.0)


def make():
    return nn.Sequential(nn.Unflatten(1, (1, 28, 28)), nn.Conv2d(1, 16, 3, padding=1), nn.BatchNorm2d(16), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(16, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
                         nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.AdaptiveAvgPool2d(1), nn.Flatten())


def train(X, Y, ncls, epochs=8):
    torch.manual_seed(0); emb = make(); head = nn.Linear(64, ncls); opt = torch.optim.Adam(list(emb.parameters()) + list(head.parameters()), lr=2e-3)
    Yt = torch.tensor(Y)
    for ep in range(epochs):
        emb.train(); perm = torch.randperm(len(X))
        for i in range(0, len(X), 128):
            b = perm[i:i + 128]; opt.zero_grad(); nn.functional.cross_entropy(head(emb(X[b])), Yt[b]).backward(); opt.step()
    emb.eval(); return emb


def embed(emb, X):
    with torch.no_grad(): z = torch.cat([emb(X[i:i + 1000]) for i in range(0, len(X), 1000)])
    return nn.functional.normalize(z, dim=1).numpy()


t0 = time.time()
for variant in ("old", "old+fsdd"):
    old = np.where(ytr < 5)[0]
    if variant == "old":
        X, Y, nc = Ptr[old], ytr[old], 5
    else:
        X = torch.cat([Ptr[old], Pfs]); Y = np.concatenate([ytr[old], yfs + 5]); nc = 15
    emb = train(X, Y, nc); ztr, zte = embed(emb, Ptr), embed(emb, Pte)
    print(variant, "embedding trained", round(time.time() - t0), "s; closed-set accuracy on old words (head-free prototypes):", flush=True)
    for k in (1, 5):
        rows = []
        for s in (1, 2, 3):
            g = np.random.RandomState(1000 * s)
            proto = [ztr[ytr == c].mean(0) for c in range(5)] + [ztr[np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False)])].mean(0) for c in range(5, 10)]
            proto = np.stack(proto); proto /= np.linalg.norm(proto, axis=1, keepdims=True); p = (zte @ proto.T).argmax(1); nw = yte >= 5
            rows.append(((p == yte).mean(), (p[nw] == yte[nw]).mean(), (p[~nw] == yte[~nw]).mean(), (p[nw] < 5).mean()))
        a = np.mean(rows, 0); print(f"GPU-style ({variant}) k={k}: all-10 {a[0]:.3f}  new {a[1]:.3f}  old {a[2]:.3f}  new->old {a[3]:.3f}", flush=True)
