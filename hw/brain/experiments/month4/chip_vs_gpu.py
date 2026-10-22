#!/usr/bin/env python3
"""Chip vs GPU on the same task (22 Oct 2026). One script, one data folder, one table.

  CHIP  = the integer model of the L Cortex chip (bit-exact with the RTL; runs in software on the CPU). Learns in 5 stages of 2 classes with no stored examples
          (dreams, slow table, shipped settings) and also all classes at once (one pass).
  GPU   = a small CNN (2 conv + 1 hidden layer, Adam, float32) on your GPU (CUDA if torch finds one, else CPU): trained on all classes at once, and in the same 5 stages with no help.
          The CNN is only a ruler, never part of the chip.
Both get the same training images and the same test images. The table prints accuracy and wall time; when an NVIDIA GPU and pynvml are available it also prints the GPU's measured energy (joules) for each run.
The chip's energy is NOT measured here (it is a software model): see the deck for the ESTIMATED figure.

  python chip_vs_gpu.py DATA_DIR [--ds mnist|fashion] [--per-stage 2000] [--seeds 2] [--epochs 4]
DATA_DIR holds mnist.npz (digits) or fashion-train-images-idx3-ubyte.gz etc. (clothing); the 'cortex_data' folder of the board demo works.
Needs: numpy, numba, torch (CUDA build for the GPU), optionally pynvml (pip install nvidia-ml-py)."""
import argparse, os, sys, time, threading
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", ".."))
import detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
ap = argparse.ArgumentParser(); ap.add_argument("data"); ap.add_argument("--ds", default="mnist"); ap.add_argument("--per-stage", type=int, default=2000); ap.add_argument("--seeds", type=int, default=2); ap.add_argument("--epochs", type=int, default=4); a = ap.parse_args()
STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; NPS = a.per_stage
xtr, ytr, xte, yte = load(a.data, a.ds); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
print(f"{a.ds}: {len(xtr)} training images in 5 stages of 2 classes, {len(xte)} test images", flush=True)
# ---------------------------------------------------------------- chip (integer model)
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])][:12000]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
ctr, cte = enc(xtr), enc(xte); res = {}
for staged in (False, True):
    accs, t0 = [], time.time()
    for seed in range(1, a.seeds + 1):
        m = CortexSlow(ctr.shape[1], ch=max(100, NPS >> 5), K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)
        for i, s in enumerate(STAGES if staged else [tuple(range(10))]):
            o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(ctr[o], ytr[o])
        accs.append(float((m.predict(cte) == yte).mean()))
    res[("chip", staged)] = (np.mean(accs), (time.time() - t0) / a.seeds, None)
# ---------------------------------------------------------------- GPU (CNN ruler)
import torch, torch.nn as nn
dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); print("GPU ruler runs on:", torch.cuda.get_device_name(0) if dev.type == "cuda" else "CPU (no CUDA GPU found)", flush=True)
try:
    import pynvml; pynvml.nvmlInit(); H = pynvml.nvmlDeviceGetHandleByIndex(0)
except Exception: H = None
class Meter:                                                      # GPU energy in joules: NVML total-energy counter when present, else integrated power samples
    def __enter__(self):
        self.t0 = time.time(); self.e0 = None; self.j = None; self.stop = False; self.samples = []
        if H is not None:
            try: self.e0 = pynvml.nvmlDeviceGetTotalEnergyConsumption(H)
            except Exception: self.e0 = None
            if self.e0 is None:
                def run():
                    while not self.stop: self.samples.append((time.time(), pynvml.nvmlDeviceGetPowerUsage(H) / 1000.0)); time.sleep(0.05)
                self.th = threading.Thread(target=run); self.th.start()
        return self
    def __exit__(self, *e):
        self.dt = time.time() - self.t0
        if H is not None:
            if self.e0 is not None: self.j = (pynvml.nvmlDeviceGetTotalEnergyConsumption(H) - self.e0) / 1000.0
            else:
                self.stop = True; self.th.join(); s = self.samples; self.j = sum((s[i + 1][0] - s[i][0]) * s[i][1] for i in range(len(s) - 1)) if len(s) > 1 else None
T = lambda x: torch.tensor(np.asarray(x, np.float32).reshape(-1, 1, 28, 28) / 255.0)
Xtr, Xte, Ytr, Yte = T(xtr).to(dev), T(xte).to(dev), torch.tensor(ytr).to(dev), torch.tensor(yte).to(dev)
def net(): return nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(64 * 49, 128), nn.ReLU(), nn.Linear(128, 10)).to(dev)
def fit(m, X, Y, epochs):
    opt = torch.optim.Adam(m.parameters(), 1e-3)
    for _ in range(epochs):
        p = torch.randperm(len(X), device=dev)
        for i in range(0, len(X), 64):
            b = p[i:i + 64]; opt.zero_grad(); nn.functional.cross_entropy(m(X[b]), Y[b]).backward(); opt.step()
def acc(m):
    with torch.no_grad(): return float((m(Xte).argmax(1) == Yte).float().mean())
torch.manual_seed(1)
with Meter() as mt:
    m = net(); fit(m, Xtr, Ytr, a.epochs); ac = acc(m)
    if dev.type == "cuda": torch.cuda.synchronize()
res[("gpu", False)] = (ac, mt.dt, mt.j)
with Meter() as mt:
    m = net()
    for s in STAGES:
        sel = torch.isin(Ytr, torch.tensor(s, device=dev)); fit(m, Xtr[sel], Ytr[sel], max(1, a.epochs // 2))
    ac = acc(m)
    if dev.type == "cuda": torch.cuda.synchronize()
res[("gpu", True)] = (ac, mt.dt, mt.j)
# ---------------------------------------------------------------- table
print("\n%-44s %9s %10s %12s" % ("run (same images, same test set)", "accuracy", "time (s)", "GPU energy"))
for (who, staged), (ac_, t_, j_) in res.items():
    name = ("L Cortex chip model" if who == "chip" else "CNN on the GPU") + (", 5 stages, no stored examples" if staged else ", all classes at once")
    print("%-44s %8.2f%% %10.1f %12s" % (name, 100 * ac_, t_, "n/a" if j_ is None else "%.0f J" % j_))
print("\nChip time is the software model on the CPU, not the chip. Chip energy is not measured here (ESTIMATED on the deck). The CNN is a ruler only.")
