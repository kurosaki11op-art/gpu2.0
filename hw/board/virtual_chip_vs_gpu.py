#!/usr/bin/env python3
"""Virtual chip vs GPU on the same task (22 Oct 2026).

  VIRTUAL CHIP = the Tang Nano 20K top-level design (cortex_board_top.v: UART + core + encoder) running in an RTL simulator (Icarus Verilog) on this PC. It is taught digits 0-3 in four stages by sending it the real board's UART bytes and then asked to recognise held-out
                 test digits; its answers come back as reply bytes (rtl_board_demo.py). The integer model must give the same bytes (bit-exact).
  GPU          = a small CNN on your GPU (CUDA if found), trained on the SAME training images (all four digits at once, and in the same four stages with no help) and tested on the SAME test images.
Both answer the same test images; the table shows accuracy and time. The CNN is only a ruler. Not a measurement of the real board: the virtual chip is a logic simulation.

  python virtual_chip_vs_gpu.py DATA_DIR [--per-class 80] [--test 15] [--epochs 20]
Needs: Icarus Verilog (iverilog and vvp on PATH), numpy, numba, torch. DATA_DIR holds mnist.npz and sep_mnist_F32_p2.npz (made by hw/brain/proof_suite_v3.py; or run this once with --make-sep to build it)."""
import argparse, os, subprocess, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "brain"))
ap = argparse.ArgumentParser(); ap.add_argument("data"); ap.add_argument("--per-class", type=int, default=80); ap.add_argument("--test", type=int, default=15); ap.add_argument("--epochs", type=int, default=20); ap.add_argument("--make-sep", action="store_true"); a = ap.parse_args()
from cortex_core import load
if a.make_sep or not os.path.exists(os.path.join(a.data, "sep_mnist_F32_p2.npz")):
    import detector_learn
    xtr, ytr, xte, yte = load(a.data, "mnist"); ytr = ytr.astype(np.int64)
    fes = detector_learn.learn_features(xtr[np.isin(ytr, (0, 1))][:12000]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
    np.savez_compressed(os.path.join(a.data, "sep_mnist_F32_p2.npz"), tr=enc(xtr), te=enc(xte)); print("built sep_mnist_F32_p2.npz", flush=True)
# ---- 1. the virtual chip: the board design in RTL simulation
env = dict(os.environ, NPER=str(a.per_class), NTEST=str(a.test), DREAMS="2"); t0 = time.time()
print("virtual chip: simulating the Tang Nano top-level design (this takes a while) ...", flush=True)
r = subprocess.run([sys.executable, os.path.join(HERE, "rtl_board_demo.py"), a.data], env=env, capture_output=True, text=True, cwd=HERE); print(r.stdout.strip().splitlines()[-4:] if r.stdout else r.stderr[-500:])
t_chip = time.time() - t0; sp = np.load(os.path.join(HERE, "demo_split.npz"))
xtr, ytr, xte, yte = load(a.data, "mnist"); tr, trY, te, ans = sp["train"], sp["train_y"], sp["test"], sp["answers"]; chip_acc = float((ans == yte[te]).mean())
# ---- 2. the GPU: a CNN on the same images
import torch, torch.nn as nn
dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); print("GPU ruler runs on:", torch.cuda.get_device_name(0) if dev.type == "cuda" else "CPU (no CUDA GPU found)", flush=True)
T = lambda x: torch.tensor(np.asarray(x, np.float32).reshape(-1, 1, 28, 28) / 255.0).to(dev)
Xtr, Ytr, Xte, Yte = T(xtr[tr]), torch.tensor(trY).to(dev), T(xte[te]), torch.tensor(yte[te].astype(np.int64)).to(dev)
def net(): return nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(64 * 49, 128), nn.ReLU(), nn.Linear(128, 10)).to(dev)
def fit(m, X, Y, ep):
    opt = torch.optim.Adam(m.parameters(), 1e-3)
    for _ in range(ep):
        p = torch.randperm(len(X), device=dev)
        for i in range(0, len(X), 16): b = p[i:i + 16]; opt.zero_grad(); nn.functional.cross_entropy(m(X[b]), Y[b]).backward(); opt.step()
def acc(m):
    with torch.no_grad(): return float((m(Xte).argmax(1) == Yte).float().mean())
torch.manual_seed(1); t0 = time.time(); m = net(); fit(m, Xtr, Ytr, a.epochs); a_joint = acc(m); t_joint = time.time() - t0
t0 = time.time(); m = net()
for c in range(4): sel = Ytr == c; fit(m, Xtr[sel], Ytr[sel], max(1, a.epochs // 4))
a_stage = acc(m); t_stage = time.time() - t0
print("\n%-58s %9s %9s" % (f"same {a.per_class} images per digit (0-3), same {len(te)} test images", "accuracy", "time (s)"))
print("%-58s %8.1f%% %9.0f" % ("virtual chip (board design in RTL simulation), 4 stages, no stored examples", 100 * chip_acc, t_chip))
print("%-58s %8.1f%% %9.1f" % ("GPU CNN, all four digits at once", 100 * a_joint, t_joint))
print("%-58s %8.1f%% %9.1f" % ("GPU CNN, the same four stages, no help", 100 * a_stage, t_stage))
print("\nThe virtual chip's time is a logic simulation on this PC, not the speed of the real chip. The CNN is a ruler, never part of the chip.")
