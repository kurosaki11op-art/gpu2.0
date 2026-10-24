"""Few-example learning on REAL colour photos (Grigorev clothing dataset: T-Shirt, Shirt, Longsleeve, Outwear), 24 Oct 2026, SIMULATED/MEASURED on CPU.
Same methods as learning_curve4: fast brain (class means on L's code), exemplars, counting table, sum, CNN with a self-supervised encoder (autoencoder on UNLABELLED training photos), random 75/25 split (fixed), 3 draws of n labelled photos per class.
L code: three colour planes, each 32 detectors x 4 channels, pool 4 (13,824 bits), detectors fitted on unlabelled training photos. usage: python learning_curve_photos.py /tmp/clothing"""
import sys, os, numpy as np, torch, torch.nn as nn
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features
from cortex_slow import CortexSlow
torch.set_num_threads(3); D = sys.argv[1]; z0 = np.load(D + "/arr.npz"); X28, y = z0["a"], z0["y"]; names = ["T-Shirt", "Shirt", "Longsleeve", "Outwear"]
r = np.random.RandomState(0); perm = r.permutation(len(y)); cut = int(0.75 * len(y)); tr, te = perm[:cut], perm[cut:]; ytr, yte = y[tr], y[te]
CH = (50, 150, ("on", 8), ("off", 8)); planes = lambda a: [a[..., k].reshape(len(a), -1) for k in range(3)]
Ptr, Pte = planes(X28[tr]), planes(X28[te]); ctrs, ctes = [], []
for p, q in zip(Ptr, Pte):
    fes = [Features(32, thr=c, pool=4).fit(p[:3000]) for c in CH]; enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 200]) for g in fes], 1) for i in range(0, len(x), 200)])
    ctrs.append(enc(p)); ctes.append(enc(q))
ctr, centre = np.concatenate(ctrs, 1).astype(np.int32), np.concatenate(ctes, 1).astype(np.int32); print("photos: train %d test %d, code bits %d, classes %s" % (len(tr), len(te), ctr.shape[1], np.bincount(ytr)), flush=True)
nc = 4; z = lambda a: (a - a.mean(1, keepdims=True)) / (a.std(1, keepdims=True) + 1e-6); acc = lambda sc: (sc.argmax(1) == yte).mean(); bal = lambda p: np.mean([(p[yte == c] == c).mean() for c in range(nc)])
def proto(idx): P = np.stack([ctr[idx][ytr[idx] == c].mean(0) for c in range(nc)]).astype(np.float32); return centre.astype(np.float32) @ P.T / (np.sqrt((P ** 2).sum(1))[None, :] + 1e-6)
def table(idx):
    m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(0).permutation(len(idx)); m.stage(ctr[idx][sel], ytr[idx][sel]); return (centre @ m.S.astype(np.int32).T).astype(np.float32)[:, :nc]
Xi_tr = torch.tensor(X28[tr].transpose(0, 3, 1, 2) / 255.0, dtype=torch.float32); Xi_te = torch.tensor(X28[te].transpose(0, 3, 1, 2) / 255.0, dtype=torch.float32)
torch.manual_seed(0); enc_net = nn.Sequential(nn.Conv2d(3, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU())
dec = nn.Sequential(nn.ConvTranspose2d(64, 32, 2, stride=2), nn.ReLU(), nn.ConvTranspose2d(32, 16, 2, stride=2), nn.ReLU(), nn.Conv2d(16, 3, 3, padding=1), nn.Sigmoid()); opt = torch.optim.Adam(list(enc_net.parameters()) + list(dec.parameters()), 2e-3)
for ep in range(40):
    pm = torch.randperm(len(Xi_tr))
    for i in range(0, len(Xi_tr), 64): b = Xi_tr[pm[i:i + 64]]; loss = nn.functional.mse_loss(dec(enc_net(b)), b); opt.zero_grad(); loss.backward(); opt.step()
def cnn_ssl(idx):
    with torch.no_grad(): ftr = enc_net(Xi_tr[idx]).flatten(1); fte = enc_net(Xi_te).flatten(1)
    mu, sd = ftr.mean(0), ftr.std(0) + 1e-3; ftr, fte = (ftr - mu) / sd, (fte - mu) / sd; Y = torch.tensor(ytr[idx]); torch.manual_seed(0); head = nn.Linear(ftr.shape[1], nc); o = torch.optim.Adam(head.parameters(), 1e-2, weight_decay=1e-2)
    for _ in range(200): loss = nn.functional.cross_entropy(head(ftr), Y); o.zero_grad(); loss.backward(); o.step()
    with torch.no_grad(): return head(fte).numpy()
meths = {"fast: class means": lambda i: proto(i), "slow table": lambda i: table(i), "sum of 2": lambda i: z(proto(i)) + z(table(i)), "CNN, self-supervised encoder": lambda i: cnn_ssl(i)}
print("balanced accuracy (mean recall over the 4 classes) and Shirt recall; chance 25%\n| labelled photos per class | " + " | ".join(meths) + " |\n|---|" + "---|" * len(meths), flush=True)
for n in (1, 2, 5, 10, 20, 50):
    res = {k: [] for k in meths}
    for seed in range(3):
        rr = np.random.RandomState(2000 + seed); idx = np.concatenate([rr.choice(np.where(ytr == c)[0], min(n, int((ytr == c).sum())), replace=False) for c in range(nc)])
        for k, f in meths.items(): sc = f(idx); p = sc.argmax(1); res[k].append((bal(p), (p[yte == 1] == 1).mean()))
    print("| %d | " % n + " | ".join("%.1f (Shirt %.0f)" % (100 * np.mean([a for a, _ in v]), 100 * np.mean([b for _, b in v])) for v in res.values()) + " |", flush=True)
