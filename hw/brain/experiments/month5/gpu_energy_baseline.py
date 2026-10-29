"""28 Oct 2026. GPU ENERGY BASELINE for the clothing recognition task (to be run by the founder on a machine with an NVIDIA GPU; written and tested here only on the CPU path, because the build container has no GPU). Trains the reference convolutional network (32 filters of 3 x 3, 2 x 2 max pool, one linear layer, the same shape as the project's reference CNN) on Fashion-MNIST, then measures inference energy per image on the GPU at several batch sizes and precisions by sampling the GPU's own power sensor (NVML, through pynvml or nvidia-smi) while a timed loop runs, and subtracting the idle power measured first. Results are MEASURED (GPU sensor, this machine) once run on a GPU; the accuracy is MEASURED on the test set. Usage: python gpu_energy_baseline.py DATA_DIR [--epochs 10] [--seconds 10] [--cpu]
DATA_DIR holds fashion-train-images-idx3-ubyte.gz and its three companions (the same folder the repo's checks use). Output: a table and gpu_energy_baseline.json next to the script. The power sensor reads the whole board (GPU plus memory), not the chip alone; this is stated in the output."""
import argparse, json, os, subprocess, sys, threading, time
import numpy as np, torch, torch.nn as nn
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "brain"))
from cortex_core import load
ap = argparse.ArgumentParser(); ap.add_argument("data_dir"); ap.add_argument("--epochs", type=int, default=10); ap.add_argument("--seconds", type=float, default=10.0); ap.add_argument("--cpu", action="store_true"); ap.add_argument("--batches", default="1,64,1024"); ap.add_argument("--net", default="tiny", choices=["tiny", "small", "strong"]); a = ap.parse_args()   # small / strong = the two reference networks of cnn_confidence.py, so the measured energy matches the accuracy and operation-count comparison
torch.backends.cudnn.benchmark = True
dev = "cpu" if (a.cpu or not torch.cuda.is_available()) else "cuda"
xtr, ytr, xte, yte = load(a.data_dir, "fashion"); f = lambda x: torch.tensor(x.reshape(-1, 1, 28, 28), dtype=torch.float32) / 255.0
Xtr, Ytr, Xte, Yte = f(xtr).to(dev), torch.tensor(ytr, dtype=torch.long).to(dev), f(xte).to(dev), torch.tensor(yte, dtype=torch.long).to(dev)
NETS = {"tiny": lambda: nn.Sequential(nn.Conv2d(1, 32, 3), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(13 * 13 * 32, 10)),
        "small": lambda: nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Dropout(0.3), nn.Linear(64 * 49, 10)),
        "strong": lambda: nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.Conv2d(32, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Dropout(0.4), nn.Linear(64 * 49, 256), nn.ReLU(), nn.Dropout(0.4), nn.Linear(256, 10))}
model = NETS[a.net]().to(dev); opt = torch.optim.Adam(model.parameters(), 1e-3)
for ep in range(a.epochs):
    perm = torch.randperm(len(Xtr), device=dev)
    for i in range(0, len(Xtr), 128): j = perm[i:i + 128]; opt.zero_grad(); nn.functional.cross_entropy(model(Xtr[j]), Ytr[j]).backward(); opt.step()
model.eval()
with torch.no_grad(): acc = (model(Xte).argmax(1) == Yte).float().mean().item()
print("device %s, float32 test accuracy %.4f (%d epochs)" % (dev, acc, a.epochs), flush=True)
class Power:
    """Samples board power in watts every ~20 ms from NVML (pynvml) or nvidia-smi."""
    def __init__(self):
        self.ok = False; self.h = None
        if dev == "cuda":
            try: import pynvml; pynvml.nvmlInit(); self.h = pynvml.nvmlDeviceGetHandleByIndex(0); self.nv = pynvml; self.ok = True; self.name = pynvml.nvmlDeviceGetName(self.h)
            except Exception: self.ok = False
    def read(self):
        if self.ok: return self.nv.nvmlDeviceGetPowerUsage(self.h) / 1000.0
        try: return float(subprocess.check_output(["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits"]).decode().split()[0])
        except Exception: return None
    def run(self, fn, seconds):
        samples = []; stop = threading.Event()
        def sampler():
            while not stop.is_set():
                p = self.read(); samples.append((time.time(), p))
                stop.wait(0.25)   # slow sampling: on Windows an NVML query can stall the driver and starve the kernel launches (seen on a laptop RTX 3050: 5 images/s)
        th = threading.Thread(target=sampler); th.start(); t0 = time.time(); n = 0
        while time.time() - t0 < seconds: n += fn()
        if dev == "cuda": torch.cuda.synchronize()
        dt = time.time() - t0; stop.set(); th.join(); return n, dt, [p for _, p in samples if p is not None]
def raw_rate(bs, seconds=3.0):
    """images per second with NO power sampling and a synchronise after every step: the true speed of the GPU for this network"""
    for _ in range(10):
        with torch.no_grad(): model(Xte[:bs]).argmax(1)
    if dev == "cuda": torch.cuda.synchronize()
    t0 = time.time(); n = 0
    while time.time() - t0 < seconds:
        with torch.no_grad(): model(Xte[:bs]).argmax(1)
        if dev == "cuda": torch.cuda.synchronize()
        n += bs
    return n / (time.time() - t0)
RAW = {bs: raw_rate(bs) for bs in [int(v) for v in a.batches.split(",")]}
print("raw speed without power sampling (images/s): " + ", ".join("batch %d: %.0f" % (b, r) for b, r in RAW.items()), flush=True)
pw = Power(); out = {"net": a.net, "device": dev, "accuracy_float32": acc, "epochs": a.epochs, "results": []}
if dev == "cuda": out["gpu"] = torch.cuda.get_device_name(0)
idle = None
if dev == "cuda":
    _, _, s = pw.run(lambda: time.sleep(0.05) or 0, 5.0); idle = float(np.mean(s)) if s else None; out["idle_watts"] = idle; print("idle power %s W" % ("%.1f" % idle if idle else "unavailable"), flush=True)
print("%-10s %-8s %10s %12s %12s %14s %14s" % ("precision", "batch", "images/s", "mean W", "net W", "mJ/image net", "mJ/image gross"))
for prec in (["fp32", "fp16"] if dev == "cuda" else ["fp32"]):
    for bs in [int(v) for v in a.batches.split(",")]:
        idx = [0]
        def step(bs=bs, prec=prec):
            i = idx[0]; idx[0] = (i + bs) % (len(Xte) - bs); x = Xte[i:i + bs]
            with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.float16, enabled=(prec == "fp16" and dev == "cuda")): model(x).argmax(1)
            if dev == "cuda": torch.cuda.synchronize()
            return bs
        for _ in range(20): step()
        if dev == "cuda": torch.cuda.synchronize()
        n, dt, s = pw.run(step, a.seconds); thr = n / dt; mp = float(np.mean(s)) if s else None
        net = (mp - idle) if (mp is not None and idle is not None) else None
        rec = {"precision": prec, "batch": bs, "raw_images_per_s": RAW.get(bs), "images_per_s": thr, "mean_watts": mp, "net_watts": net, "mJ_per_image_net": (1000 * net / thr) if net is not None else None, "mJ_per_image_gross": (1000 * mp / thr) if mp is not None else None}
        out["results"].append(rec); print("%-10s %-8d %10.0f %12s %12s %14s %14s" % (prec, bs, thr, "%.1f" % mp if mp else "n/a", "%.1f" % net if net is not None else "n/a", "%.4f" % rec["mJ_per_image_net"] if rec["mJ_per_image_net"] is not None else "n/a", "%.4f" % rec["mJ_per_image_gross"] if rec["mJ_per_image_gross"] is not None else "n/a"), flush=True)
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gpu_energy_baseline_%s.json" % a.net), "w"), indent=1); print("wrote gpu_energy_baseline_<net>.json. Power is the whole GPU board as the sensor reports it.")
