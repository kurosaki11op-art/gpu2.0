"""29 Oct 2026, SIMULATED (accuracy), reference baselines only (not parts of L). (1) Risk-coverage of two reference CNNs (a small one, 8 epochs; a stronger one with shift+flip augmentation, 12 epochs) using their own confidence (margin of the logits, and max softmax probability), next to the chip's (margin of final integer scores).
(2) Fixability: how do the CNNs do on the images the chip gets wrong, and on the 20% it flags? If they get them right, there is headroom; if they fail too, the images are hard for any model at this resolution. One seed each. Logits are saved to the scratchpad."""
import sys, time
sys.argv = ["x", "/tmp/fashion"]; sys.path.insert(0, "/home/user/gpu2.0/hw/brain/experiments/month5")
import numpy as np, torch, torch.nn as nn
from shirt_new_methods_setup import xtr, xte, ytr, yte, NAMES
import ldeep_ref as R
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"
torch.manual_seed(0); torch.set_num_threads(3); t0 = time.time()
A = torch.tensor(xtr.reshape(-1, 1, 28, 28) / 255.0, dtype=torch.float32); y = torch.tensor(ytr); T = torch.tensor(xte.reshape(-1, 1, 28, 28) / 255.0, dtype=torch.float32)
def train(net, epochs, aug, tag):
    opt = torch.optim.Adam(net.parameters(), lr=1e-3); sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, epochs)
    for ep in range(epochs):
        net.train(); perm = torch.randperm(len(y))
        for i in range(0, len(y), 128):
            ix = perm[i:i + 128]; xb = A[ix]
            if aug:
                if torch.rand(1) < 0.5: xb = xb.flip(3)
                dx, dy = np.random.randint(-2, 3, 2); xb = torch.roll(xb, (int(dy), int(dx)), (2, 3))
            opt.zero_grad(); nn.functional.cross_entropy(net(xb), y[ix]).backward(); opt.step()
        sched.step()
    net.eval()
    with torch.no_grad(): lg = torch.cat([net(T[i:i + 1000]) for i in range(0, len(T), 1000)]).numpy()
    print("%-34s accuracy %.4f [%.0fs]" % (tag, (lg.argmax(1) == yte).mean(), time.time() - t0), flush=True); np.save(SP + "logits_%s.npy" % tag.split()[0], lg); return lg
small = nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Dropout(0.3), nn.Linear(64 * 49, 10))
strong = nn.Sequential(nn.Conv2d(1, 32, 3, padding=1), nn.ReLU(), nn.Conv2d(32, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.Conv2d(64, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2), nn.Flatten(), nn.Dropout(0.4), nn.Linear(64 * 49, 256), nn.ReLU(), nn.Dropout(0.4), nn.Linear(256, 10))
Ls = train(small, 8, False, "small CNN (8 epochs)"); Lg = train(strong, 12, True, "strong CNN (12 epochs, augmented)")
z = np.load(SP + "deep_test_all.npz"); X = np.ascontiguousarray(z["X"], np.uint8); rr, S, pp = R.run(X); srt = np.sort(S, 1); chip_m = (srt[:, -1] - srt[:, -2]).astype(np.float64); chip_ok = pp == yte
def curve(score, ok): o = np.argsort(-score, kind="stable"); return [ok[o[:int(round((1 - f) * len(ok)))]].mean() for f in (0, .05, .1, .2, .3, .4)]
def lm(lg): s = np.sort(lg, 1); return s[:, -1] - s[:, -2]
def mp(lg): e = np.exp(lg - lg.max(1, keepdims=True)); return (e / e.sum(1, keepdims=True)).max(1)
print("\\naccuracy on the answered images when the least-sure share is flagged:")
print("%-44s" % "share flagged" + "".join("%9s" % ("%d%%" % f) for f in (0, 5, 10, 20, 30, 40)))
print("%-44s" % "chip (L + L Deep), margin" + "".join("%9.4f" % v for v in curve(chip_m, chip_ok)))
for nm, lg in (("small CNN", Ls), ("strong CNN", Lg)):
    ok = lg.argmax(1) == yte
    print("%-44s" % (nm + ", logit margin") + "".join("%9.4f" % v for v in curve(lm(lg), ok))); print("%-44s" % (nm + ", max softmax") + "".join("%9.4f" % v for v in curve(mp(lg), ok)))
print("\\nfixability: the chip's %d errors on the test set" % (~chip_ok).sum()); fl = np.argsort(-chip_m, kind="stable")[int(0.8 * len(yte)):]
for nm, lg in (("small CNN", Ls), ("strong CNN", Lg)):
    ok = lg.argmax(1) == yte; both = (~chip_ok & ~ok).sum(); print("%-11s right on %.1f%% of the chip's errors; wrong on both: %d (%.1f%% of all images); on the chip's flagged 20%%: CNN accuracy %.3f vs chip %.3f" % (nm, 100 * ok[~chip_ok].mean(), both, 100 * both / len(yte), ok[fl].mean(), chip_ok[fl].mean()))
ok2 = Lg.argmax(1) == yte; print("oracle (chip or strong CNN right): %.4f; wrong on both: per class " % (chip_ok | ok2).mean() + ", ".join("%s %d" % (NAMES[c], (~chip_ok & ~ok2 & (yte == c)).sum()) for c in range(10) if (~chip_ok & ~ok2 & (yte == c)).sum() > 0))
