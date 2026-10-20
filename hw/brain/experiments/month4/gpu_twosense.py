"""GPU-style reference for the two-sense tests (20 Oct 2026). A DIAGNOSTIC ruler, not part of the chip. Same data as brain_strict_twosense*.py: 10,000 MNIST training images / 2,000 test images, FSDD spoken digits (6 speakers; test speaker = the last; the ear is trained on speakers 0-2, the clips heard with the pictures come from speakers 3-4), the same 28x28 aligned sound pictures.
Small CNNs (float32, Adam, backprop):
  A  image CNN, true labels
  B  image CNN, zero image labels: trained on the names a sound CNN gives to the clips heard with each picture
  B+ as B, then 2 rounds of self-training (relabel every image with the model's own prediction, retrain from scratch): the usual GPU recipe for noisy labels
  D  two-tower CNN (image tower + sound tower, features concatenated) trained on the pairs with true labels; tested with both senses, with the picture damaged (25 % of its lit pixels removed) with and without the sound, and with a blank sound
usage: DATA_DIR"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, torch, torch.nn as nn
import cochlea_int
from noise_floor import picture as _picture
from cortex_core import load
D = sys.argv[1]; t0 = time.time(); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; torch.manual_seed(1); SEEDS = int(os.environ.get("SEEDS", 2))
xtr, ytr, xte, yte = load(D, "mnist"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]; ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
z = np.load(os.path.join(D, "fsdd_framesums_int.npz")); S, sy, spk = z["S"], z["y"].astype(np.int64), z["spk"]; stest = spk == spk.max()
pic = cochlea_int.align_word(_picture(S, "low4x4"), 6).astype(np.float32).reshape(-1, 1, 28, 28); pic = pic / max(1.0, float(np.percentile(pic, 99.5)))
T = lambda x: torch.tensor(np.asarray(x, np.float32).reshape(-1, 1, 28, 28) / 255.0)
Vtr, Vte = T(xtr), T(xte); Atr, Ate = torch.tensor(pic[~stest]), torch.tensor(pic[stest]); satr, sate = sy[~stest], sy[stest]; sptr = spk[~stest]


def tower(): return nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(64 * 49, 128), nn.ReLU())


def net(): return nn.Sequential(tower(), nn.Linear(128, 10))


class Two(nn.Module):
    def __init__(self): super().__init__(); self.v, self.a, self.h = tower(), tower(), nn.Linear(256, 10)
    def forward(self, v, a): return self.h(torch.cat([self.v(v), self.a(a)], 1))


def fit(m, X, Y, epochs=12, two=None):
    opt = torch.optim.Adam(m.parameters(), 1e-3); n = len(Y)
    for _ in range(epochs):
        p = torch.randperm(n)
        for i in range(0, n, 64):
            b = p[i:i + 64]; opt.zero_grad(); out = m(X[b]) if two is None else m(X[b], two[b]); nn.functional.cross_entropy(out, Y[b]).backward(); opt.step()
    return m


def acc(m, X, y, two=None):
    with torch.no_grad(): p = (m(X) if two is None else m(X, two)).argmax(1).numpy()
    return float((p == y).mean())


R = {}
for seed in range(1, SEEDS + 1):
    torch.manual_seed(seed); r = np.random.RandomState(seed)
    ear = fit(net(), Atr[sptr <= 2], torch.tensor(satr[sptr <= 2]), 25); pool = np.where(sptr >= 3)[0]
    pair = np.array([r.choice(pool[satr[pool] == d]) for d in ytr])
    with torch.no_grad(): names = ear(Atr[pair]).argmax(1).numpy()
    R.setdefault("ear's names correct (CNN ear, unseen speakers)", []).append(float((names == ytr).mean()))
    R.setdefault("A image CNN, true labels", []).append(acc(fit(net(), Vtr, torch.tensor(ytr)), Vte, yte))
    mb = fit(net(), Vtr, torch.tensor(names)); R.setdefault("B image CNN, zero image labels (ear's names)", []).append(acc(mb, Vte, yte))
    lab = names; m = mb
    for rd in range(2):
        with torch.no_grad(): lab = m(Vtr).argmax(1).numpy()
        m = fit(net(), Vtr, torch.tensor(lab))
    R.setdefault("B+ image CNN, ear's names + 2 rounds of self-training", []).append(acc(m, Vte, yte)); R.setdefault("  B+ names correct after self-training", []).append(float((lab == ytr).mean()))
    allp = np.arange(len(satr)); pair2 = np.array([r.choice(allp[satr == d]) for d in ytr]); two = fit(Two(), Vtr, torch.tensor(ytr), 12, two=Atr[pair2])
    tp = np.array([r.choice(np.where(sate == d)[0]) for d in yte]); ta = Ate[tp]; blank = torch.zeros_like(ta); dam = Vte * (torch.rand_like(Vte) >= 0.25).float()
    for k, (v, a) in {"D two-tower, both senses": (Vte, ta), "D picture damaged 25 % + sound": (dam, ta), "D picture damaged 25 %, sound blank": (dam, blank), "D picture only (sound blank)": (Vte, blank), "D sound only (picture blank)": (torch.zeros_like(Vte), ta)}.items():
        R.setdefault(k, []).append(acc(two, v, yte, two=a))
    print("seed", seed, "%.0fs" % (time.time() - t0), flush=True)
for k, v in R.items(): print("%-62s %.4f" % (k, np.mean(v)), flush=True)
