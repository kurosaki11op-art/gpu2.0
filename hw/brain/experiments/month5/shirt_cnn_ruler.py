"""Ruler: how well does a small CNN (trained with backprop on all 60,000 images, 6 epochs) separate Shirt from T-shirt? (24 Oct 2026, MEASURED on CPU, one seed)
Never part of the chip; it only shows what is achievable on 28x28 clothing images. usage: python shirt_cnn_ruler.py DATA_DIR"""
import sys, os, time, numpy as np, torch, torch.nn as nn
sys.path.insert(0, "/home/user/gpu2.0/hw/brain"); from cortex_core import load
xtr, ytr, xte, yte = load(sys.argv[1], "fashion"); torch.manual_seed(0); torch.set_num_threads(4)
f = lambda x: torch.tensor(x.reshape(-1, 1, 28, 28) / 255.0, dtype=torch.float32)
Xtr, Xte = f(xtr), f(xte); Ytr = torch.tensor(ytr.astype(np.int64)); Yte = yte.astype(np.int64)
m = nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(64 * 49, 128), nn.ReLU(), nn.Linear(128, 10))
opt = torch.optim.Adam(m.parameters(), 2e-3); t0 = time.time()
for ep in range(6):
    perm = torch.randperm(len(Xtr))
    for i in range(0, len(Xtr), 256):
        b = perm[i:i + 256]; loss = nn.functional.cross_entropy(m(Xtr[b]), Ytr[b]); opt.zero_grad(); loss.backward(); opt.step()
with torch.no_grad(): p = torch.cat([m(Xte[i:i + 2000]).argmax(1) for i in range(0, len(Xte), 2000)]).numpy()
names = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat", "Sandal", "Shirt", "Sneaker", "Bag", "Boot"]
print("overall %.4f (%.0fs)" % ((p == Yte).mean(), time.time() - t0))
for k in range(10): print("  %-9s recall %.3f" % (names[k], (p[Yte == k] == k).mean()))
g = np.isin(Yte, (0, 2, 4, 6)); P = np.array((0, 2, 4, 6))[0]  # placeholder
print("Shirt predicted as T-shirt: %d of 1000, T-shirt predicted as Shirt: %d of 1000" % ((p[Yte == 6] == 0).sum(), (p[Yte == 0] == 6).sum()))
