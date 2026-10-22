"""CNN ruler for the 20-class problem (22 Oct 2026), a DIAGNOSTIC, never in the chip. Same data as brain_strict_classes20.py (10 digits + 10 clothing classes, 2,000 images per stage of 2 classes, full 20,000 test images). All classes together (4 epochs) and 10 stages with no help (2 epochs per stage). usage: DATA_DIR"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, torch, torch.nn as nn
from cortex_core import load
D = sys.argv[1]; NPS = int(os.environ.get("NPS", 2000)); torch.manual_seed(1)
a = load(D, "mnist"); b = load(D, "fashion")
xtr = np.concatenate([a[0], b[0]]); ytr = np.concatenate([a[1].astype(np.int64), b[1].astype(np.int64) + 10]); xte = np.concatenate([a[2], b[2]]); yte = np.concatenate([a[3].astype(np.int64), b[3].astype(np.int64) + 10])
STAGES = [(2 * i, 2 * i + 1) for i in range(10)]; rs = np.random.RandomState(5)
idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
T = lambda x: torch.tensor(np.asarray(x, np.float32).reshape(-1, 1, 28, 28) / 255.0)
Xtr, Xte, Ytr, Yte = T(xtr), T(xte), torch.tensor(ytr), torch.tensor(yte)
def net(): return nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(64 * 49, 128), nn.ReLU(), nn.Linear(128, 20))
def fit(m, X, Y, epochs):
    opt = torch.optim.Adam(m.parameters(), 1e-3)
    for _ in range(epochs):
        p = torch.randperm(len(X))
        for i in range(0, len(X), 64):
            bb = p[i:i + 64]; opt.zero_grad(); nn.functional.cross_entropy(m(X[bb]), Y[bb]).backward(); opt.step()
def acc(m):
    with torch.no_grad(): p = m(Xte).argmax(1)
    return float((p == Yte).float().mean()), float((p == Yte)[Yte < 10].float().mean()), float((p == Yte)[Yte >= 10].float().mean())
m = net(); fit(m, Xtr, Ytr, 4); print("20 classes CNN joint (all, digits, clothing)", [round(v, 4) for v in acc(m)], flush=True)
m = net()
for s in STAGES: fit(m, Xtr[np.isin(ytr, s)], Ytr[np.isin(ytr, s)], 2)
print("20 classes CNN in stages, no help (all, digits, clothing)", [round(v, 4) for v in acc(m)], flush=True)
