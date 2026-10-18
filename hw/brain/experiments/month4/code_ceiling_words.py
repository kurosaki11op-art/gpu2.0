"""Ceiling for spoken words: floating-point networks (diagnostic, not the chip) on the chip's aligned sound code (F64, 23040 bits) and on the aligned
28x28 sound pictures (784 values), all ten words at once, 1 seed. usage: DATA_DIR. SIMULATED diagnostic."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, torch, torch.nn as nn
from sound_align_confirm import align
torch.set_num_threads(2); torch.manual_seed(0)
D = sys.argv[1]
f = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = f["S"], f["y"], f["te"]
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz"))
P = align(S, 6).astype(np.float32) / 255.0
ytr, yte = torch.tensor(y[~te].astype(np.int64)), torch.tensor(y[te].astype(np.int64))


def fit(model, Xtr, Xte, epochs=15, lr=2e-3):
    opt = torch.optim.Adam(model.parameters(), lr=lr); n = len(Xtr)
    for ep in range(epochs):
        perm = torch.randperm(n)
        for i in range(0, n, 128):
            b = perm[i:i + 128]; opt.zero_grad(); nn.functional.cross_entropy(model(Xtr[b]), ytr[b]).backward(); opt.step()
    model.eval()
    with torch.no_grad(): return float((model(Xte).argmax(1) == yte).float().mean())


out = {}; t0 = time.time()
Ctr, Cte = torch.tensor(z["tr"], dtype=torch.float32), torch.tensor(z["te"], dtype=torch.float32)
out["code_linear"] = fit(nn.Linear(Ctr.shape[1], 10), Ctr, Cte); print("code linear", out["code_linear"], time.time() - t0, flush=True)
out["code_mlp256"] = fit(nn.Sequential(nn.Linear(Ctr.shape[1], 256), nn.ReLU(), nn.Linear(256, 10)), Ctr, Cte); print("code mlp", out["code_mlp256"], time.time() - t0, flush=True)
Ptr, Pte = torch.tensor(P[~te]), torch.tensor(P[te])
out["pictures_mlp256"] = fit(nn.Sequential(nn.Linear(784, 256), nn.ReLU(), nn.Linear(256, 10)), Ptr, Pte); print("pictures mlp", out["pictures_mlp256"], time.time() - t0, flush=True)
cnn = nn.Sequential(nn.Unflatten(1, (1, 28, 28)), nn.Conv2d(1, 16, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(16, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(32 * 49, 10))
out["pictures_cnn"] = fit(cnn, Ptr, Pte); print("pictures cnn", out["pictures_cnn"], time.time() - t0, flush=True)
json.dump({"label": "SIMULATED diagnostic: floating-point networks with backprop, not part of the chip; 1 seed", **{k: round(v, 4) for k, v in out.items()}}, open("code_ceiling_words.json", "w"), indent=1)
