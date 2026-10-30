"""30 Oct 2026, SIMULATED. TARGET 1 FIRST DECISIVE TEST: learning NEW classes from a few examples, on a device, against a GPU-style network. Fashion-MNIST. The device (L Cortex integer model CortexSlow, bit-exact with the RTL) and a small reference CNN are both trained on 8 classes, then 2 NEW classes arrive with only k examples each (k = 1, 5, 20, 100; 3 random draws each).
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
for new in ((8, 9), (4, 6)):
    old = [c for c in range(10) if c not in new]; print("\\nNEW classes %s (the other 8 are known)" % ", ".join(NAMES[c] for c in new), flush=True)
    mchip = chip_base(old); bcnn = cnn_base(old); pc = cnn_eval(bcnn); pch = np.where(np.isin(np.arange(10), old)[None, :], mchip.predict(cte)[:, None] == np.arange(10)[None, :], False)
    print("  before the new classes: chip old-class accuracy %.4f | CNN old-class accuracy %.4f [%.0fs]" % ((mchip.predict(cte)[np.isin(yte, old)] == yte[np.isin(yte, old)]).mean(), (pc[np.isin(yte, old)] == yte[np.isin(yte, old)]).mean(), time.time() - t0), flush=True)
    print("  %-4s | %-28s | %-28s | %-28s" % ("k", "CHIP (dreams, no stored data)", "CNN fine-tune, new data only", "CNN + 20 stored old / class"), flush=True)
    print("  %-4s | %-8s %-9s %-9s | %-8s %-9s %-9s | %-8s %-9s %-9s" % ("", "all", "old", "new", "all", "old", "new", "all", "old", "new"), flush=True)
    for k in KS:
        res = {"chip": [], "cnn": [], "cnnr": []}
        for draw in range(3):
            r = np.random.RandomState(1000 * k + draw); sel = np.concatenate([r.choice(np.nonzero(ytr == c)[0], k, replace=False) for c in new]); r.shuffle(sel)
            m2 = copy.deepcopy(mchip); m2.stage(ctr[sel], ytr[sel]); res["chip"].append(scores(m2.predict(cte), old, new))
            res["cnn"].append(scores(cnn_finetune(bcnn, xtr[sel], ytr[sel]), old, new))
            rep = np.concatenate([r.choice(np.nonzero(ytr == c)[0], 20, replace=False) for c in old]); both = np.concatenate([sel, rep]); res["cnnr"].append(scores(cnn_finetune(bcnn, xtr[both], ytr[both]), old, new))
        f = lambda a: "%-8.3f %-9.3f %-9.3f" % tuple(np.mean(a, 0)); print("  %-4d | %s | %s | %s" % (k, f(res["chip"]), f(res["cnn"]), f(res["cnnr"])), flush=True)
print("\\n[%.0fs] done" % (time.time() - t0))
