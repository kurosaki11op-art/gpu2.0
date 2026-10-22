#!/usr/bin/env python3
"""Virtual space benchmark (22 Oct 2026): the L Cortex chip (virtual: its RTL design in a simulator) and a GPU, one table.

  CHIP (virtual)  cycles per decision / learn / dream measured in RTL simulation of cortex_core.v at the real size (4,608 code bits, about 263 active), converted to time at the board clock (27 MHz) and the pipelined build. SIMULATED cycles, MODELLED times.
                  Energy per decision: the deck's ESTIMATED figure (9.4 nJ, operation count), printed for comparison; it is not measured.
  GPU (yours)     a small CNN (2 conv + 1 hidden layer) deciding the same digit images: latency at batch 1, throughput at a large batch, and the GPU's MEASURED energy per decision (NVML) when an NVIDIA GPU and nvidia-ml-py are present.
  The two do different work (the chip is a counting table, the CNN is a trained network), so this is a speed and energy comparison of doing a decision, not an identical computation. Accuracy of the two on the same task: python hw/board/virtual_chip_vs_gpu.py (option --accuracy here).

  python virtual_space/benchmark.py DATA_DIR [--mhz 27] [--accuracy]       DATA_DIR holds mnist.npz"""
import argparse, os, subprocess, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(HERE, ".."); sys.path.insert(0, os.path.join(ROOT, "hw", "brain"))
ap = argparse.ArgumentParser(); ap.add_argument("data"); ap.add_argument("--mhz", type=float, default=27.0); ap.add_argument("--accuracy", action="store_true"); ap.add_argument("--batch", type=int, default=1024); a = ap.parse_args()
from cortex_core import load
sep = os.path.join(a.data, "sep_mnist_F32_p2.npz")
if not os.path.exists(sep):
    import detector_learn
    xtr, ytr, xte, yte = load(a.data, "mnist"); ytr = ytr.astype(np.int64); fes = detector_learn.learn_features(xtr[np.isin(ytr, (0, 1))][:12000])
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)]); np.savez_compressed(sep, tr=enc(xtr), te=enc(xte)); print("built", sep, flush=True)
# ---------------------------------------------------------------- the virtual chip: cycle counts from the RTL
print("virtual chip: measuring cycles in RTL simulation (about a minute) ...", flush=True)
r = subprocess.run([sys.executable, os.path.join(ROOT, "hw", "rtl", "cortex", "run_chip_bench.py"), a.data, "--n", "2", "--mhz", str(a.mhz)], capture_output=True, text=True)
print(r.stdout.strip() if r.returncode == 0 else r.stderr[-800:], flush=True)
cyc = {}
for l in r.stdout.splitlines():
    p = l.split()
    if l.startswith("FPGA build"): cyc["fpga"] = [float(x) for x in p[2:5]]
    if l.startswith("pipelined"): cyc["pipe"] = [float(x) for x in p[3:6]]
# ---------------------------------------------------------------- the GPU
import torch, torch.nn as nn
dev = torch.device("cuda" if torch.cuda.is_available() else "cpu"); name = torch.cuda.get_device_name(0) if dev.type == "cuda" else "CPU (no CUDA GPU found)"; print("\nGPU side runs on:", name, flush=True)
try:
    import pynvml; pynvml.nvmlInit(); H = pynvml.nvmlDeviceGetHandleByIndex(0); pynvml.nvmlDeviceGetTotalEnergyConsumption(H)
except Exception: H = None
xtr, ytr, xte, yte = load(a.data, "mnist")
def net(): return nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(64 * 49, 128), nn.ReLU(), nn.Linear(128, 10)).to(dev).eval()
m = net(); sync = (lambda: torch.cuda.synchronize()) if dev.type == "cuda" else (lambda: None)
X1 = torch.tensor(xte[:1].astype(np.float32).reshape(-1, 1, 28, 28) / 255.0).to(dev); XB = torch.tensor(xte[:a.batch].astype(np.float32).reshape(-1, 1, 28, 28) / 255.0).to(dev)
with torch.no_grad():
    for _ in range(20): m(X1)
    sync(); t0 = time.time(); N1 = 300
    for _ in range(N1): m(X1)
    sync(); lat = (time.time() - t0) / N1
    for _ in range(5): m(XB)
    sync(); e0 = pynvml.nvmlDeviceGetTotalEnergyConsumption(H) if H else None; t0 = time.time(); NB_ = 30
    for _ in range(NB_): m(XB)
    sync(); dt = time.time() - t0; e1 = pynvml.nvmlDeviceGetTotalEnergyConsumption(H) if H else None
    ips = NB_ * len(XB) / dt; ej = (e1 - e0) / 1000.0 / (NB_ * len(XB)) if H else None
    e0 = pynvml.nvmlDeviceGetTotalEnergyConsumption(H) if H else None; t0 = time.time(); NR = 600
    for _ in range(NR): m(X1)
    sync(); e1 = pynvml.nvmlDeviceGetTotalEnergyConsumption(H) if H else None; ej1 = (e1 - e0) / 1000.0 / NR if H else None
# ---------------------------------------------------------------- the table
print("\n" + "=" * 100); print("DECIDING ONE DIGIT IMAGE".ljust(48), "latency".rjust(12), "decisions/s".rjust(13), "energy per decision".rjust(22)); print("=" * 100)
if "fpga" in cyc:
    t = cyc["fpga"][2] / (a.mhz * 1e6); print(("virtual chip, FPGA build, %.0f MHz (SIMULATED cycles)" % a.mhz).ljust(48), ("%.1f us" % (t * 1e6)).rjust(12), ("%.0f" % (1 / t)).rjust(13), "9.4 nJ (ESTIMATED)".rjust(22))
if "pipe" in cyc:
    t = cyc["pipe"][2] / (a.mhz * 1e6); print(("virtual chip, pipelined (ASIC option), %.0f MHz" % a.mhz).ljust(48), ("%.1f us" % (t * 1e6)).rjust(12), ("%.0f" % (1 / t)).rjust(13), "9.4 nJ (ESTIMATED)".rjust(22))
print(("%s, batch 1 (MEASURED)" % name[:30]).ljust(48), ("%.1f us" % (lat * 1e6)).rjust(12), ("%.0f" % (1 / lat)).rjust(13), ("%.2f mJ (MEASURED)" % (ej1 * 1e3) if ej1 else "n/a (no NVML)").rjust(22))
print(("%s, batch %d (MEASURED)" % (name[:26], a.batch)).ljust(48), "-".rjust(12), ("%.0f" % ips).rjust(13), ("%.3f mJ (MEASURED)" % (ej * 1e3) if ej else "n/a (no NVML)").rjust(22))
print("=" * 100)
print("The chip rows are the design running in a simulator: cycle counts are exact, times are modelled at the stated clock, energy is the deck's estimate. The GPU rows are measured on this machine. The chip does one decision per 'stream'; a real product could run many.")
if a.accuracy:
    subprocess.run([sys.executable, os.path.join(ROOT, "hw", "board", "virtual_chip_vs_gpu.py"), a.data, "--per-class", "80", "--test", "15", "--epochs", "20"])
