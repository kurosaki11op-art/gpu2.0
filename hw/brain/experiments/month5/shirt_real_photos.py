"""Shirt against T-shirt on real colour photos (24 Oct 2026). Data: Grigorev clothing dataset (user photos, colour, 400+ px; github alexeygrigorev/clothing-dataset,
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
CH = (50, 150, ("on", 8), ("off", 8))
def Lcodes(planes_tr, planes_te):                         # planes: list of (N, 784) uint8
    outs_tr, outs_te = [], []
    for ptr, pte in zip(planes_tr, planes_te):
        fes = [Features(32, thr=c, pool=4).fit(ptr[:3000]) for c in CH]
        enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 300]) for g in fes], 1) for i in range(0, len(x), 300)])
        outs_tr.append(enc(ptr)); outs_te.append(enc(pte))
    return np.concatenate(outs_tr, 1).astype(np.int32), np.concatenate(outs_te, 1).astype(np.int32)
def L_run(ctr, ytr, cte, nc):
    m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(1).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel])
    return (cte @ m.S.T.astype(np.int32))[:, :nc].argmax(1)
import torch, torch.nn as nn
torch.set_num_threads(4)
def cnn_run(xtr, ytr, xte, nc, epochs=40):
    torch.manual_seed(0); c = xtr.shape[1]; s = xtr.shape[2]
    m = nn.Sequential(nn.Conv2d(c, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(), nn.AdaptiveAvgPool2d(3), nn.Flatten(), nn.Linear(576, 64), nn.ReLU(), nn.Linear(64, nc))
    opt = torch.optim.Adam(m.parameters(), 2e-3); X = torch.tensor(xtr, dtype=torch.float32); Y = torch.tensor(ytr)
    for ep in range(epochs):
        perm = torch.randperm(len(X))
        for i in range(0, len(X), 64):
            b = perm[i:i + 64]; xb = X[b]; xb = torch.where(torch.rand(len(b), 1, 1, 1) < 0.5, xb.flip(3), xb)
            loss = nn.functional.cross_entropy(m(xb), Y[b]); opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad(): return m(torch.tensor(xte, dtype=torch.float32)).argmax(1).numpy()
def grey(x): return (x.astype(np.float32) @ np.array([0.299, 0.587, 0.114], np.float32)).astype(np.uint8)
def chw(x): return (x.transpose(0, 3, 1, 2) / 255.0)
for task, keep in (("Shirt vs T-Shirt (2-way)", (0, 1)), ("4-way: T-Shirt, Shirt, Longsleeve, Outwear", (0, 1, 2, 3))):
    idx = np.where(np.isin(y, keep))[0]; yy = y[idx]; nc = len(keep); print("\n" + task, "n =", len(idx), flush=True)
    res = {}
    for split in range(5):
        r = np.random.RandomState(split); perm = r.permutation(len(idx)); cut = int(0.75 * len(idx)); tr, te = perm[:cut], perm[cut:]
        a28, a56 = X28[idx], X56[idx]
        g = grey(a28).reshape(len(idx), -1)
        runs = {}
        runs["L grey 28"] = L_run(*(lambda c: (c[0], yy[tr], c[1]))(Lcodes([g[tr]], [g[te]])), nc)
        pl = [a28[..., k].reshape(len(idx), -1) for k in range(3)]
        runs["L colour 28"] = L_run(*(lambda c: (c[0], yy[tr], c[1]))(Lcodes([p[tr] for p in pl], [p[te] for p in pl])), nc)
        runs["CNN grey 28"] = cnn_run(chw(a28)[tr][:, :1] * 0 + (g[tr].reshape(-1, 1, 28, 28) / 255.0), yy[tr], g[te].reshape(-1, 1, 28, 28) / 255.0, nc)
        runs["CNN colour 28"] = cnn_run(chw(a28)[tr], yy[tr], chw(a28)[te], nc)
        runs["CNN colour 56"] = cnn_run(chw(a56)[tr], yy[tr], chw(a56)[te], nc)
        for k, p in runs.items():
            res.setdefault(k, []).append([(p[yy[te] == c] == c).mean() for c in range(nc)] + [(p == yy[te]).mean()])
        print(" split", split, {k: round(float(v[-1][-1]), 3) for k, v in res.items()}, flush=True)
    print("| input | " + " | ".join(CL[c] + " recall" for c in keep) + " | accuracy |\n|---|" + "---|" * (nc + 1))
    for k, v in res.items(): m = np.mean(v, 0); print("| %s | " % k + " | ".join("%.3f" % x for x in m) + " |", flush=True)
