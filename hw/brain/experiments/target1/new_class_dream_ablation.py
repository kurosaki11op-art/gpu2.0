"""30 Oct 2026, SIMULATED. (Part 2: dream-count ablation of new_class_learning_test.py.) How many night dreams of the old classes does the chip need when a new class arrives, and what does each count cost in accuracy? TARGET 1 FIRST DECISIVE TEST: learning NEW classes from a few examples, on a device, against a GPU-style network. Fashion-MNIST. The device (L Cortex integer model CortexSlow, bit-exact with the RTL) and a small reference CNN are both trained on 8 classes, then 2 NEW classes arrive with only k examples each (k = 1, 5, 20, 100; 3 random draws each).
Chip: its own staged on-chip learning (LEARN, dreams of old classes instead of stored data, FOLLOW), no stored old examples. CNN: fine-tuned on the k new examples (a) alone and (b) with a replay buffer of 20 stored old examples per class (the CNN needs stored data to resist forgetting; the chip dreams it).
Reports accuracy on the whole 10-class test set, on the old classes (forgetting) and on the new classes. New-class splits: (Bag, Ankle boot) = easy classes, and (Coat, Shirt) = hard, confusable classes."""
import copy, sys, time
sys.argv = ["x", "/tmp/fashion"]; sys.path.insert(0, "/home/user/gpu2.0/hw/brain/experiments/month5"); sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import numpy as np, torch, torch.nn as nn
from shirt_new_methods_setup import ctr, cte, xtr, xte, ytr, yte, NAMES
from cortex_slow import CortexSlow
torch.manual_seed(0); torch.set_num_threads(3); t0 = time.time(); KS = (1, 5, 20, 100)
def chip_base(old):
    idx = np.nonzero(np.isin(ytr, old))[0]; idx = idx[np.random.RandomState(100).permutation(len(idx))]
    m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); m.stage(ctr[idx], ytr[idx]); return m
def cnn_net(): return nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Dropout(0.3), nn.Linear(64 * 49, 10))
X = lambda a: torch.tensor(a.reshape(-1, 1, 28, 28) / 255.0, dtype=torch.float32)
def cnn_base(old):
    idx = np.nonzero(np.isin(ytr, old))[0]; A, y = X(xtr[idx]), torch.tensor(ytr[idx]); net = cnn_net(); opt = torch.optim.Adam(net.parameters(), 1e-3)
    for ep in range(8):
        net.train(); perm = torch.randperm(len(y))
        for i in range(0, len(y), 128): ix = perm[i:i + 128]; opt.zero_grad(); nn.functional.cross_entropy(net(A[ix]), y[ix]).backward(); opt.step()
    return net
T = X(xte)
def scores(pred, old, new):
    ok = pred == yte; mo, mn = np.isin(yte, old), np.isin(yte, new); return ok.mean(), ok[mo].mean(), ok[mn].mean()
def cnn_eval(net):
    net.eval()
    with torch.no_grad(): return net(T).argmax(1).numpy()
def cnn_finetune(base, xs, ys, steps=100):
    net = copy.deepcopy(base); net.train(); opt = torch.optim.Adam(net.parameters(), 1e-3); A, y = X(xs), torch.tensor(ys)
    for s in range(steps): opt.zero_grad(); nn.functional.cross_entropy(net(A), y).backward(); opt.step()
    return cnn_eval(net)

print("night dreams per old class (ndream): accuracy after learning the new classes from k examples (all / old / new), mean of 2 draws; dream count = ndream x old classes x 2 nights", flush=True)
for new in ((8, 9), (4, 6)):
    old = [c for c in range(10) if c not in new]; mchip = chip_base(old); print("\nNEW classes %s [%.0fs]" % (", ".join(NAMES[c] for c in new), time.time() - t0), flush=True)
    print("  %-6s %-6s | %-9s %-9s %-9s | dreams in the stage" % ("k", "ndream", "all", "old", "new"), flush=True)
    for k in (5, 20, 100):
        for nd in (6000, 1500, 300, 60):
            res = []
            for draw in range(2):
                r = np.random.RandomState(1000 * k + draw); sel = np.concatenate([r.choice(np.nonzero(ytr == c)[0], k, replace=False) for c in new]); r.shuffle(sel)
                m2 = copy.deepcopy(mchip); m2.ndream = nd; m2.stage(ctr[sel], ytr[sel]); res.append(scores(m2.predict(cte), old, new))
            print("  %-6d %-6d | %-9.3f %-9.3f %-9.3f | %d" % ((k, nd) + tuple(np.mean(res, 0)) + (nd * len(old) * 2,)), flush=True)
print("[%.0fs] done" % (time.time() - t0))
