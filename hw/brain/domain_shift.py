"""Domain-incremental test: day 1 = all ten digits upright, day 2 = all ten digits rotated 90 degrees (same classes,
new condition). After day 2, accuracy on upright AND rotated test digits. Integer chip model (month-2 rule; the
sensory detectors are the ones learned from upright 0/1 images) vs a network fine-tuned day by day.
usage: python domain_shift.py DATA_DIR [mnist|fashion]"""
import json, os, sys
import numpy as np, torch
from cortex_int import CortexInt
from cortex_core import load
from feature_layer import Features
D, DS = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "mnist")
xtr, ytr, xte, yte = load(D, DS); ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
rot = lambda x: np.rot90(x.reshape(-1, 28, 28), 1, axes=(1, 2)).reshape(-1, 784).copy()
fes = [Features(32, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
h = len(xtr) // 2
dayA, dayB = np.arange(h), np.arange(h, len(xtr))                       # different images on each day
cA, cB = enc(xtr[dayA]), enc(rot(xtr[dayB])); tU, tR = enc(xte), enc(rot(xte))
R = {"dataset": DS, "label": "SIMULATED"}
for tag, ctx in (("chip", False), ("chip_context_memory", True)):
    m = CortexInt(cA.shape[1], B=10, night=2, daydream=1, night_stop=2, context=ctx)
    m.stage(cA, ytr[dayA]); R[tag + "_after_day1"] = {"upright": float((m.predict(tU) == yte).mean()), "rotated": float((m.predict(tR) == yte).mean())}
    m.stage(cB, ytr[dayB]); R[tag + "_after_day2"] = {"upright": float((m.predict(tU) == yte).mean()), "rotated": float((m.predict(tR) == yte).mean())}
torch.manual_seed(0); net = torch.nn.Sequential(torch.nn.Linear(784, 256), torch.nn.ReLU(), torch.nn.Linear(256, 10))
opt = torch.optim.Adam(net.parameters(), 1e-3)
def fit(x, y):
    X = torch.tensor(x / 255.0, dtype=torch.float32); Y = torch.tensor(y)
    for _ in range(2):
        for b in torch.randperm(len(X)).split(64):
            opt.zero_grad(); torch.nn.functional.cross_entropy(net(X[b]), Y[b]).backward(); opt.step()
def ev(x):
    with torch.no_grad():
        return float((net(torch.tensor(x / 255.0, dtype=torch.float32)).argmax(1).numpy() == yte).mean())
fit(xtr[dayA], ytr[dayA]); R["net_after_day1"] = {"upright": ev(xte), "rotated": ev(rot(xte))}
fit(rot(xtr[dayB]), ytr[dayB]); R["net_after_day2"] = {"upright": ev(xte), "rotated": ev(rot(xte))}
print(json.dumps(R, indent=1))
json.dump(R, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", f"cortex_domain_shift_{DS}.json"), "w"), indent=1)
