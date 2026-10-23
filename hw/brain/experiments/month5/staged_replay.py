"""Fair continual-learning baselines for the staged test (24 Oct 2026) SIMULATED/MEASURED on CPU, torch.
Same protocol as L Cortex: 5 stages of 2 classes, 2,000 images per stage (random), accuracy on ALL classes after the last stage (and after each stage).
Methods for the 784-256-128-10 MLP: fine-tuning (no protection), replay of N stored examples per old class (N = 10, 50, 200, 1000), EWC (lambda sweep), joint training (upper bound, all five stages at once).
Replay memory = stored pixels (8 bits each), reported in KB so it can be set against L's deployed table (11 to 45 KB) and L's learning state.
usage: python staged_replay.py DATA_DIR [fashion|mnist]"""
import sys, os, gzip, numpy as np, torch, torch.nn as nn
torch.set_num_threads(4); D = sys.argv[1]; DS = sys.argv[2] if len(sys.argv) > 2 else "fashion"; P = "fashion-" if DS == "fashion" else ""
if DS == "mnist":
    z = np.load(os.path.join(D, "mnist.npz")); Xtr, ytr, Xte, yte = z["x_train"].reshape(-1, 784), z["y_train"], z["x_test"].reshape(-1, 784), z["y_test"]
else:
    rd = lambda f, o: np.frombuffer(gzip.open(os.path.join(D, P + f)).read(), np.uint8, offset=o)
    Xtr = rd("train-images-idx3-ubyte.gz", 16).reshape(-1, 784); ytr = rd("train-labels-idx1-ubyte.gz", 8); Xte = rd("t10k-images-idx3-ubyte.gz", 16).reshape(-1, 784); yte = rd("t10k-labels-idx1-ubyte.gz", 8)
f = lambda x: torch.tensor(x / 255.0, dtype=torch.float32)
Xtr_t, Xte_t = f(Xtr), f(Xte); ytr_t, yte_t = torch.tensor(ytr.astype(np.int64)), torch.tensor(yte.astype(np.int64))
STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; NPS = 2000; EP = 10
def net(): return nn.Sequential(nn.Linear(784, 256), nn.ReLU(), nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 10))
def acc(m):
    with torch.no_grad(): return float((m(Xte_t).argmax(1) == yte_t).float().mean()) * 100
def fit(m, X, y, ep, ewc=None, lam=0.0, seed=0):
    opt = torch.optim.Adam(m.parameters(), 1e-3); g = torch.Generator().manual_seed(seed)
    for _ in range(ep):
        perm = torch.randperm(len(X), generator=g)
        for i in range(0, len(X), 128):
            b = perm[i:i + 128]; loss = nn.functional.cross_entropy(m(X[b]), y[b])
            if ewc and lam: loss = loss + lam * sum((F * (p - p0) ** 2).sum() for (F, p0), p in zip(ewc, m.parameters())) / 2
            opt.zero_grad(); loss.backward(); opt.step()
def fisher(m, X, y):
    F = [torch.zeros_like(p) for p in m.parameters()]
    for i in range(min(len(X), 500)):
        m.zero_grad(); nn.functional.cross_entropy(m(X[i:i + 1]), y[i:i + 1]).backward()
        for Fi, p in zip(F, m.parameters()): Fi += p.grad.detach() ** 2 / min(len(X), 500)
    return F
def stage_idx(seed, s): r = np.random.RandomState(seed * 10 + s); idx = np.where(np.isin(ytr, STAGES[s]))[0]; return torch.tensor(r.permutation(idx)[:NPS])
res = {}
for seed in (1, 2, 3):
    torch.manual_seed(seed)
    def run(method, N=0, lam=0.0):
        m = net(); buf_x, buf_y = [], []; ewc = None; curve = []
        for s in range(5):
            ix = stage_idx(seed, s); X, y = Xtr_t[ix], ytr_t[ix]
            if method == "replay" and buf_x: X, y = torch.cat([X] + buf_x), torch.cat([y] + buf_y)
            fit(m, X, y, EP, ewc=ewc, lam=lam, seed=seed); curve.append(acc(m))
            if method == "replay":
                for c in STAGES[s]: sel = (ytr_t[ix] == c).nonzero().flatten()[:N]; buf_x.append(Xtr_t[ix][sel]); buf_y.append(ytr_t[ix][sel])
            if method == "ewc":
                F = fisher(m, Xtr_t[ix], ytr_t[ix]); p0 = [p.detach().clone() for p in m.parameters()]
                ewc = [(F[i] + (ewc[i][0] if ewc else 0), p0[i]) for i in range(len(F))]
        return curve
    for name, kw in (("fine-tuning", dict(method="ft")), ("replay 10/class (%.0f KB)" % (10 * 10 * 784 / 1024), dict(method="replay", N=10)), ("replay 50/class (%.0f KB)" % (50 * 10 * 784 / 1024), dict(method="replay", N=50)),
                     ("replay 200/class (%.0f KB)" % (200 * 10 * 784 / 1024), dict(method="replay", N=200)), ("replay 1000/class (%.0f KB)" % (1000 * 10 * 784 / 1024), dict(method="replay", N=1000)),
                     ("EWC lambda 100", dict(method="ewc", lam=100.0)), ("EWC lambda 10000", dict(method="ewc", lam=1e4))):
        res.setdefault(name, []).append(run(**kw)); print(seed, name, ["%.1f" % v for v in res[name][-1]], flush=True)
    m = net(); ix = torch.cat([stage_idx(seed, s) for s in range(5)]); fit(m, Xtr_t[ix], ytr_t[ix], EP, seed=seed); res.setdefault("joint (upper bound)", []).append([acc(m)]); print(seed, "joint", res["joint (upper bound)"][-1], flush=True)
print("\n%s, MLP, 5 stages x 2 classes, %d images per stage, %d epochs per stage, mean of 3 seeds, accuracy on ALL classes after the last stage:" % (DS, NPS, EP))
print("| method | final accuracy % | std |\n|---|---|---|")
for k, v in res.items(): a = np.array([x[-1] for x in v]); print("| %s | %.1f | %.1f |" % (k, a.mean(), a.std()))
print("L Cortex, same protocol: digits 94.2, clothing 81.5 (earlier runs; stores no examples; deployed table 11 to 45 KB)")
