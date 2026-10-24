"""Sparse-fan-in binary convolutional net with an L-style counting readout (accelerator path B), 24 Oct 2026, SIMULATED on CPU, torch.
Feature layers: each filter reads only n taps (fixed random mask) of its 3x3 window, weights real during training, activation = sign (1 bit, straight-through), so after training every neuron
is an n-bit lookup table (2^n entries); max-pool = OR. Readout: sparse sums of int8 table rows (like L's decision rule), here a linear table over the flattened bits.
Training (backprop) on CPU/GPU; inference = lookups, ORs and adds. usage: python binconv.py DATA_DIR [epochs]"""
import sys, os, gzip, time, numpy as np, torch, torch.nn as nn
torch.set_num_threads(4); D = sys.argv[1]; EPOCHS = int(sys.argv[2]) if len(sys.argv) > 2 else 10
F1, F2, n = int(os.environ.get("F1", 64)), int(os.environ.get("F2", 128)), int(os.environ.get("NIN", 8))
rd = lambda f, o: np.frombuffer(gzip.open(os.path.join(D, "fashion-" + f)).read(), np.uint8, offset=o)
Xtr = rd("train-images-idx3-ubyte.gz", 16).reshape(-1, 28, 28); ytr = rd("train-labels-idx1-ubyte.gz", 8).astype(np.int64); Xte = rd("t10k-images-idx3-ubyte.gz", 16).reshape(-1, 28, 28); yte = rd("t10k-labels-idx1-ubyte.gz", 8).astype(np.int64)
TH = (40, 100, 160, 220); enc = lambda x: torch.tensor(np.stack([(x > t) for t in TH], 1).astype(np.float32)); Etr, Ete = enc(Xtr), enc(Xte); Ytr = torch.tensor(ytr)
class Sign(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x): ctx.save_for_backward(x); return (x > 0).float()
    @staticmethod
    def backward(ctx, g): (x,) = ctx.saved_tensors; return g * (x.abs() < 1).float()
class Sparse(nn.Module):
    def __init__(self, cin, F, seed):
        super().__init__(); g = torch.Generator().manual_seed(seed); self.conv = nn.Conv2d(cin, F, 3, padding=1)
        m = torch.zeros(F, cin * 9)
        for f in range(F): m[f, torch.randperm(cin * 9, generator=g)[:(n if n > 0 else cin * 9)]] = 1
        self.register_buffer("mask", m.view(F, cin, 3, 3)); self.bn = nn.BatchNorm2d(F)
    def forward(self, x): return Sign.apply(self.bn(nn.functional.conv2d(x, self.conv.weight * self.mask, self.conv.bias, padding=1)))
net = nn.Sequential(Sparse(len(TH), F1, 1), nn.MaxPool2d(2), Sparse(F1, F2, 2), nn.MaxPool2d(2), nn.Flatten(), nn.Linear(F2 * 49, 10))
opt = torch.optim.Adam(net.parameters(), 2e-3); sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, EPOCHS * (len(Etr) // 128 + 1)); t0 = time.time()
def ev():
    net.eval()
    with torch.no_grad(): p = torch.cat([net(Ete[i:i + 1000]).argmax(1) for i in range(0, len(Ete), 1000)]).numpy()
    net.train(); return p
for ep in range(EPOCHS):
    perm = torch.randperm(len(Etr)); tl = 0; st = 0
    for i in range(0, len(Etr), 128):
        b = perm[i:i + 128]; xb = Etr[b]
        if os.environ.get('AUG'):
            xb = torch.where(torch.rand(len(b), 1, 1, 1) < 0.5, xb.flip(3), xb); dy, dx = np.random.randint(-2, 3, 2); xb = torch.roll(xb, (int(dy), int(dx)), (2, 3))
        loss = nn.functional.cross_entropy(net(xb), Ytr[b]); opt.zero_grad(); loss.backward(); opt.step(); sched.step(); tl += loss.item(); st += 1
    p = ev(); print("epoch %d | loss %.3f | accuracy %.4f | Shirt %.3f T-shirt %.3f Pullover %.3f Coat %.3f | %.0fs" % (ep + 1, tl / st, (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[yte == 0] == 0).mean(), (p[yte == 2] == 2).mean(), (p[yte == 4] == 4).mean(), time.time() - t0), flush=True)
W = net[-1].weight.detach().numpy(); print("readout %d x %d; lookup tables: %.1f KB; readout int8 %.1f KB, 2-bit %.1f KB" % (W.shape[0], W.shape[1], (F1 + F2) * 2 ** max(n, 0) / 8 / 1024, W.size / 1024, W.size / 4 / 1024))
torch.save(net.state_dict(), os.environ.get("OUT", "binconv.pt"))
