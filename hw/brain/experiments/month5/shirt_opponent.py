"""[opponent cells + held-out volunteers] Shirt against T-shirt on real colour photos (24 Oct 2026). Data: Grigorev clothing dataset (user photos, colour, 400+ px; github alexeygrigorev/clothing-dataset,
images.csv + images/*.jpg, fetched to /tmp/clothing). Classes T-Shirt (1,011), Shirt (378) [+ Longsleeve 699, Outwear 312 for the 4-way test]. No label is used at test time.
Same images, three inputs for the SAME models: grey 28x28 (like Fashion-MNIST), colour 28x28, colour 56x56 (CNN only; the L encoder is built for 28x28).
L = integer slow-table model with the stride-1 detector code (colour = the three colour planes coded separately, codes concatenated); CNN = small backprop ruler.
5 random 75/25 splits (same for both), mean recall per class. usage: python shirt_real_photos.py /tmp/clothing"""
import sys, os, csv, time, numpy as np
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
from PIL import Image
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features
from cortex_slow import CortexSlow
D = sys.argv[1]; CL = ["T-Shirt", "Shirt", "Longsleeve", "Outwear"]
rows = [r for r in csv.DictReader(open(D + "/images.csv")) if r["label"] in CL and r["kids"] == "False" and os.path.exists(D + "/img/%s.jpg" % r["image"])]
cache = D + "/arr.npz"
if os.path.exists(cache): z = np.load(cache); X28, X56, y = z["a"], z["b"], z["y"]
else:
    def prep(f, S):
        im = Image.open(f).convert("RGB"); w, h = im.size; s = max(w, h)
        c = Image.new("RGB", (s, s), tuple(int(v) for v in np.asarray(im.resize((1, 1))).reshape(3))); c.paste(im, ((s - w) // 2, (s - h) // 2))
        return np.asarray(c.resize((S, S), Image.BILINEAR))
    X28 = np.stack([prep(D + "/img/%s.jpg" % r["image"], 28) for r in rows]); X56 = np.stack([prep(D + "/img/%s.jpg" % r["image"], 56) for r in rows])
    y = np.array([CL.index(r["label"]) for r in rows]); np.savez(cache, a=X28, b=X56, y=y)
print("images", len(y), np.bincount(y), flush=True)

senders = np.array([r["sender_id"] for r in rows])
CH = (50, 150, ("on", 8), ("off", 8))
def planes(a):                                           # a: (N,28,28,3) uint8 -> dict of (N,784) uint8 planes
    f = a.astype(np.int32); R, G, B = f[..., 0], f[..., 1], f[..., 2]
    lum = ((R * 77 + G * 150 + B * 29) >> 8)
    rg = np.clip(128 + ((R - G) >> 1) * 2, 0, 255); by = np.clip(128 + ((B - ((R + G) >> 1)) >> 1) * 2, 0, 255)      # red-green and blue-yellow opponent planes: adds, shifts
    fl = lambda x: x.reshape(len(a), -1).astype(np.uint8)
    return {"lum": fl(lum), "R": fl(R), "G": fl(G), "B": fl(B), "rg": fl(rg), "by": fl(by)}
def coarse_opp(a):                                       # cheap colour code: per 4x4 block, red-green and blue-yellow sign and size in three steps: (49 blocks x 2 x 4 bits)
    f = a.astype(np.int32); R, G, B = f[..., 0], f[..., 1], f[..., 2]
    blk = lambda x: x.reshape(len(a), 7, 4, 7, 4).sum((2, 4)) >> 4                    # block means
    rg, by = blk(R) - blk(G), blk(B) - ((blk(R) + blk(G)) >> 1)
    bits = [rg > 12, rg < -12, rg > 40, rg < -40, by > 12, by < -12, by > 40, by < -40]
    return np.concatenate([b.reshape(len(a), -1) for b in bits], 1).astype(np.int32)
def lcode(plist_tr, plist_te):
    outs = [], []
    for ptr, pte in zip(plist_tr, plist_te):
        fes = [Features(32, thr=c, pool=4).fit(ptr[:3000]) for c in CH]
        enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 300]) for g in fes], 1) for i in range(0, len(x), 300)])
        outs[0].append(enc(ptr)); outs[1].append(enc(pte))
    return np.concatenate(outs[0], 1).astype(np.int32), np.concatenate(outs[1], 1).astype(np.int32)
def L_fit_pred(ctr, ytr, cte):
    m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(1).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel])
    return (cte @ m.S.T.astype(np.int32))[:, :2].argmax(1)
import torch, torch.nn as nn
torch.set_num_threads(4)
def cnn_run(xtr, ytr, xte, epochs=40):
    torch.manual_seed(0); c = xtr.shape[1]
    m = nn.Sequential(nn.Conv2d(c, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(3), nn.Flatten(), nn.Linear(576, 64), nn.ReLU(), nn.Linear(64, 2))
    opt = torch.optim.Adam(m.parameters(), 2e-3); X = torch.tensor(xtr, dtype=torch.float32); Y = torch.tensor(ytr)
    for ep in range(epochs):
        perm = torch.randperm(len(X))
        for i in range(0, len(X), 64):
            b = perm[i:i + 64]; xb = X[b]; xb = torch.where(torch.rand(len(b), 1, 1, 1) < 0.5, xb.flip(3), xb)
            loss = nn.functional.cross_entropy(m(xb), Y[b]); opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad(): return m(torch.tensor(xte, dtype=torch.float32)).argmax(1).numpy()
idx = np.where(np.isin(y, (0, 1)))[0]; yy = y[idx]; a28 = X28[idx]; sd = senders[idx]; P = planes(a28); CO = coarse_opp(a28)
def folds(mode, k=5, seed=0):
    r = np.random.RandomState(seed)
    if mode == "random":
        perm = r.permutation(len(idx)); return [(np.setdiff1d(perm, perm[i::k]), perm[i::k]) for i in range(k)]
    us = list(np.unique(sd)); r.shuffle(us); us.sort(key=lambda u: -(sd == u).sum()); bins = [[] for _ in range(k)]; load = [0] * k
    for u in us: j = int(np.argmin(load)); bins[j].append(u); load[j] += (sd == u).sum()
    return [(np.where(~np.isin(sd, b))[0], np.where(np.isin(sd, b))[0]) for b in bins]
variants = {
    "L grey (1 plane, 4,608 bits)": ("lum",), "L RGB planes (13,824)": ("R", "G", "B"),
    "L grey + opponent planes (13,824)": ("lum", "rg", "by"), "L grey + coarse opponent bits (+392)": ("lum", "COARSE")}
for mode in ("random", "held-out volunteers"):
    print("\n== split:", mode, "| 5 folds, 1,356 images, T-Shirt 984 / Shirt 372", flush=True); res = {}
    for fi, (tr, te) in enumerate(folds("random" if mode == "random" else "group")):
        print("  fold", fi, "train", len(tr), "test", len(te), "test shirts", int((yy[te] == 1).sum()), "senders in test", len(np.unique(sd[te])), flush=True)
        out = {}
        for name, pl in variants.items():
            use = [p for p in pl if p != "COARSE"]; ctr, cte = lcode([P[p][tr] for p in use], [P[p][te] for p in use])
            if "COARSE" in pl: ctr, cte = np.concatenate([ctr, CO[tr]], 1), np.concatenate([cte, CO[te]], 1)
            out[name] = L_fit_pred(ctr, yy[tr], cte)
        g = P["lum"].reshape(-1, 1, 28, 28) / 255.0
        out["CNN grey 28 (ruler)"] = cnn_run(g[tr], yy[tr], g[te]); out["CNN colour 28 (ruler)"] = cnn_run(a28.transpose(0, 3, 1, 2)[tr] / 255.0, yy[tr], a28.transpose(0, 3, 1, 2)[te] / 255.0)
        for k, p in out.items(): res.setdefault(k, []).append([(p[yy[te] == c] == c).mean() for c in (0, 1)])
    print("| model | T-Shirt recall | Shirt recall | balanced accuracy |\n|---|---|---|---|")
    for k, v in res.items(): m = np.mean(v, 0); print("| %s | %.3f | %.3f | %.3f |" % (k, m[0], m[1], m.mean()), flush=True)
