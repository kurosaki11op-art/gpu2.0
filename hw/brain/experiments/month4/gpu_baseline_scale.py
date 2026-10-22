"""(scale version, 22 Oct 2026: NPS images per stage, 10,000 test images, few epochs because of the CPU) GPU-style reference on the SAME data as the chip tests (20 Oct 2026). A DIAGNOSTIC ruler, not part of the chip. Run on a machine with torch (the cloud container has none).
Same 10,000 training images (2,000 per class pair x 5 stages, the chip tests' RandomState(5) selection) and same 2,000 test images; a small CNN (2 conv + 1 hidden layer, Adam, float32):
  joint     all classes together, 15 epochs (the 'once' reference)
  naive     5 stages of 2 classes, each stage trained 5 epochs on its own data only (what a GPU does without help)
  replay    as naive, with a replay buffer of RB real images (default 160 = about the chip's 129 KB of memory at 784 bytes per image) kept from earlier stages
usage: python gpu_baseline_same_data.py DATA_DIR [DS=fashion|mnist]; prints accuracy and parameter count."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, torch, torch.nn as nn
from cortex_core import load
D = sys.argv[1]; DS = sys.argv[2] if len(sys.argv) > 2 else "fashion"; RB = int(os.environ.get("RB", 160)); NPS = int(os.environ.get("NPS", 12000)); EP = int(os.environ.get("EP", 4)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; torch.manual_seed(1)
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:10000]; xte, yte = xte[ti], yte[ti]
T = lambda x: torch.tensor(np.asarray(x, np.float32).reshape(-1, 1, 28, 28) / 255.0)
Xtr, Xte, Ytr, Yte = T(xtr), T(xte), torch.tensor(ytr), torch.tensor(yte)


def net(): return nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(64 * 49, 128), nn.ReLU(), nn.Linear(128, 10))


def fit(m, X, Y, epochs):
    opt = torch.optim.Adam(m.parameters(), 1e-3)
    for _ in range(epochs):
        p = torch.randperm(len(X))
        for i in range(0, len(X), 64):
            b = p[i:i + 64]; opt.zero_grad(); nn.functional.cross_entropy(m(X[b]), Y[b]).backward(); opt.step()


def acc(m):
    with torch.no_grad(): return float((m(Xte).argmax(1) == Yte).float().mean())


m = net(); print("parameters", sum(p.numel() for p in m.parameters()), flush=True); t0 = time.time(); fit(m, Xtr, Ytr, EP); print(DS, "joint", round(acc(m), 4), "%.0fs" % (time.time() - t0), flush=True)
for name, rb in (("naive", 0),):
    m = net(); buf = np.zeros(0, np.int64)
    for s in STAGES:
        cur = np.where(np.isin(ytr, s))[0]; sel = np.concatenate([cur, buf]); fit(m, Xtr[sel], Ytr[sel], 2)
        if rb: old = np.concatenate([buf, cur]); buf = old[np.random.RandomState(7).permutation(len(old))[:rb]]
    print(DS, name, round(acc(m), 4), flush=True)
