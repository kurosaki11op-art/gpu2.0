"""How much does the chip's sensory CODE limit accuracy? Train networks (floating point, backprop: a diagnostic, not part of the chip) on
  (a) the chip's code (4608 bits), linear and 1-hidden-layer MLP;  (b) raw pixels, MLP;  (c) raw pixels, small CNN (data ceiling).
If a network on the code does no better than the chip itself, the code is the limit; if it does much better, the memory/learning rule is.
usage: DATA_DIR DS (mnist|fashion). All at once, 1 seed, 8 epochs. Label: SIMULATED diagnostic (floating point)."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, torch, torch.nn as nn
from cortex_core import load
torch.set_num_threads(os.cpu_count()); torch.manual_seed(0)
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); xtr, ytr, xte, yte = load(D, DS)
code_tr, code_te = torch.tensor(z["tr"], dtype=torch.float32), torch.tensor(z["te"], dtype=torch.float32)
px_tr, px_te = torch.tensor(xtr / 255., dtype=torch.float32), torch.tensor(xte / 255., dtype=torch.float32)
yt, ye = torch.tensor(ytr.astype(np.int64)), torch.tensor(yte.astype(np.int64))


def fit(model, Xtr, Xte, epochs=8, lr=2e-3):
    opt = torch.optim.Adam(model.parameters(), lr=lr); n = len(Xtr)
    for ep in range(epochs):
        perm = torch.randperm(n)
        for i in range(0, n, 256):
            b = perm[i:i + 256]; opt.zero_grad(); nn.functional.cross_entropy(model(Xtr[b]), yt[b]).backward(); opt.step()
    model.eval()
    with torch.no_grad(): return float((torch.cat([model(Xte[i:i + 2000]).argmax(1) for i in range(0, len(Xte), 2000)]) == ye).float().mean())


out = {}; t0 = time.time()
out["code_linear"] = fit(nn.Linear(code_tr.shape[1], 10), code_tr, code_te); print("code linear", out["code_linear"], time.time() - t0, flush=True)
out["code_mlp256"] = fit(nn.Sequential(nn.Linear(code_tr.shape[1], 256), nn.ReLU(), nn.Linear(256, 10)), code_tr, code_te); print("code mlp", out["code_mlp256"], time.time() - t0, flush=True)
out["pixels_mlp256"] = fit(nn.Sequential(nn.Linear(784, 256), nn.ReLU(), nn.Linear(256, 10)), px_tr, px_te); print("pixels mlp", out["pixels_mlp256"], time.time() - t0, flush=True)
cnn = nn.Sequential(nn.Unflatten(1, (1, 28, 28)), nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(32 * 49, 10))
out["pixels_cnn"] = fit(cnn, px_tr, px_te, epochs=5); print("pixels cnn", out["pixels_cnn"], time.time() - t0, flush=True)
json.dump({"label": "SIMULATED diagnostic: floating-point networks with backprop, not part of the chip; 1 seed", "dataset": DS, **{k: round(v, 4) for k, v in out.items()}},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"code_ceiling_{DS}.json"), "w"), indent=1)
