"""Differentiable logic gate network on Fashion-MNIST (accelerator path), 24 Oct 2026, SIMULATED/MEASURED on CPU, torch.
Recipe from Petersen et al. 2022 (arXiv 2210.08277) as read in the notes: every neuron reads 2 fixed random inputs and is one of 16 two-input logic gates;
training relaxes the gate choice to a softmax over 16 real-valued gate formulas (weights W, residual init: logit of the pass-through gate A = 5, others 0);
inference takes the argmax gate on binary inputs, so the deployed network is pure gates (AND, OR, XOR, NOT...), no multiply, no matrix, no float.
Output: popcount of each class's group of last-layer gates divided by a temperature tau. Input: thermometer-coded pixels (7 thresholds).
usage: python difflogic_fmnist.py DATA_DIR [epochs] ; env WIDTH (gates per layer), DEPTH, LR. Checkpoints each epoch (resumable)."""
import sys, os, gzip, time, numpy as np, torch, torch.nn as nn
torch.set_num_threads(4); torch.manual_seed(0); D = sys.argv[1]; EPOCHS = int(sys.argv[2]) if len(sys.argv) > 2 else 20
WIDTH, DEPTH, LR = int(os.environ.get("WIDTH", 8000)), int(os.environ.get("DEPTH", 5)), float(os.environ.get("LR", 0.01)); BS = 100
rd = lambda f, o: np.frombuffer(gzip.open(os.path.join(D, "fashion-" + f)).read(), np.uint8, offset=o)
Xtr = rd("train-images-idx3-ubyte.gz", 16).reshape(-1, 784); ytr = rd("train-labels-idx1-ubyte.gz", 8).astype(np.int64); Xte = rd("t10k-images-idx3-ubyte.gz", 16).reshape(-1, 784); yte = rd("t10k-labels-idx1-ubyte.gz", 8).astype(np.int64)
TH = (32, 64, 96, 128, 160, 192, 224); enc = lambda x: torch.tensor(np.concatenate([(x > t) for t in TH], 1).astype(np.float32)); Etr, Ete = enc(Xtr), enc(Xte); Ytr = torch.tensor(ytr)
def ops(a, b):                                   # the 16 two-input gates in their real-valued (probabilistic) form
    ab = a * b
    return torch.stack([torch.zeros_like(a), ab, a - ab, a, b - ab, b, a + b - 2 * ab, a + b - ab, 1 - (a + b - ab), 1 - (a + b - 2 * ab), 1 - b, 1 - b + ab, 1 - a, 1 - a + ab, 1 - ab, torch.ones_like(a)], -1)
class Layer(nn.Module):
    def __init__(self, nin, nout, seed):
        super().__init__(); g = torch.Generator().manual_seed(seed)
        perm = torch.cat([torch.randperm(nin, generator=g) for _ in range((2 * nout) // nin + 1)])[:2 * nout]; self.register_buffer("ia", perm[:nout]); self.register_buffer("ib", perm[nout:])
        w = torch.zeros(nout, 16); w[:, 3] = 5.0; self.W = nn.Parameter(w)              # residual initialisation: start as pass-through of input A
    def forward(self, x):
        a, b = x[:, self.ia], x[:, self.ib]
        if self.training: return (ops(a, b) * torch.softmax(self.W, -1)).sum(-1)
        g = self.W.argmax(-1); return ops(a, b).gather(-1, g.expand(len(x), -1).unsqueeze(-1)).squeeze(-1)      # hard gate on binary inputs
class Net(nn.Module):
    def __init__(self):
        super().__init__(); n = Etr.shape[1]; L = []
        for d in range(DEPTH): L.append(Layer(n, WIDTH, d)); n = WIDTH
        self.layers = nn.ModuleList(L); self.tau = (WIDTH // 10) ** 0.5 / 2
    def forward(self, x):
        for l in self.layers: x = l(x)
        return (x.view(len(x), 10, -1).sum(2) - WIDTH / 20) / self.tau
net = Net(); opt = torch.optim.Adam(net.parameters(), LR); ck = os.environ.get("CKPT", "difflogic_ckpt.pt"); ep0 = 0
if os.path.exists(ck) and not os.environ.get("FRESH"): s = torch.load(ck); net.load_state_dict(s["m"]); opt.load_state_dict(s["o"]); ep0 = s["ep"]; print("resumed", ep0, flush=True)
def evaluate():
    net.eval()
    with torch.no_grad(): p = torch.cat([net(Ete[i:i + 1000]).argmax(1) for i in range(0, len(Ete), 1000)]).numpy()
    net.train(); return p
print("gates: %d (%d layers x %d); inputs %d" % (WIDTH * DEPTH, DEPTH, WIDTH, Etr.shape[1]), flush=True); t0 = time.time()
for ep in range(ep0, EPOCHS):
    perm = torch.randperm(len(Etr)); tl = 0; st = 0; net.train()
    for i in range(0, len(Etr), BS):
        b = perm[i:i + BS]; loss = nn.functional.cross_entropy(net(Etr[b]), Ytr[b]); opt.zero_grad(); loss.backward(); opt.step(); tl += loss.item(); st += 1
        if os.environ.get("BENCH") and st == 20: print("20 steps %.1fs" % (time.time() - t0), flush=True); sys.exit()
    p = evaluate(); print("epoch %d | loss %.3f | HARD-gate test accuracy %.4f | Shirt %.3f T-shirt %.3f Pullover %.3f Coat %.3f | %.0fs" % (ep + 1, tl / st, (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[yte == 0] == 0).mean(), (p[yte == 2] == 2).mean(), (p[yte == 4] == 4).mean(), time.time() - t0), flush=True)
    torch.save({"m": net.state_dict(), "o": opt.state_dict(), "ep": ep + 1}, ck)
