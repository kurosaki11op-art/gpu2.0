"""Convolutional logic-gate network on Fashion-MNIST (accelerator track), 24 Oct 2026, SIMULATED/MEASURED on CPU, torch. Recipe as read in the papers (arXiv 2210.08277 and 2411.04732):
every node is one of 16 two-input logic gates; training relaxes the choice to a softmax over the 16 real-valued gate formulas (residual start: the pass-through-A logit is 5); inference takes the argmax gate on bits, so the deployed network is pure gates (AND, OR, XOR, NOT ...), no multiply, no matrix.
Layer 1 and 2: convolutional gate TREES (7 nodes: 4 + 2 + 1, reading 8 random taps of a 3 x 3 window over all input channels), gate choices shared across positions, then 2 x 2 OR pooling. Then 2 fully connected gate layers with random pairing and a group-sum (popcount per class) divided by a temperature.
usage: python gatenet.py DATA_DIR  (env: BUDGET seconds per call (default 540), K1, K2, W1, W2, LR). Resumable: state in gatenet_ckpt.pt every 100 steps."""
import sys, os, gzip, time, numpy as np, torch, torch.nn as nn, torch.nn.functional as Fn
torch.set_num_threads(4); D = sys.argv[1]; BUDGET = float(os.environ.get("BUDGET", 540)); t_start = time.time()
K1, K2, W1, W2, LR, BS = int(os.environ.get("K1", 24)), int(os.environ.get("K2", 48)), int(os.environ.get("W1", 3000)), int(os.environ.get("W2", 2000)), float(os.environ.get("LR", 0.02)), 100
CK = os.environ.get("CKPT", "gatenet_ckpt.pt")
rd = lambda f, o: np.frombuffer(gzip.open(os.path.join(D, "fashion-" + f)).read(), np.uint8, offset=o)
Xtr = rd("train-images-idx3-ubyte.gz", 16).reshape(-1, 28, 28); ytr = rd("train-labels-idx1-ubyte.gz", 8).astype(np.int64); Xte = rd("t10k-images-idx3-ubyte.gz", 16).reshape(-1, 28, 28); yte = rd("t10k-labels-idx1-ubyte.gz", 8).astype(np.int64)
DEV = torch.device(os.environ.get('DEVICE', 'cuda' if torch.cuda.is_available() else 'cpu')); print('device', DEV, flush=True)
TH = (32, 96, 160, 224); enc = lambda x: torch.tensor(np.stack([(x > t) for t in TH], 1).astype(np.float32)); Etr, Ete = enc(Xtr).to(DEV), enc(Xte).to(DEV); Ytr = torch.tensor(ytr).to(DEV)
def formulas(a, b):
    ab = a * b
    return [torch.zeros_like(a), ab, a - ab, a, b - ab, b, a + b - 2 * ab, a + b - ab, 1 - (a + b - ab), 1 - (a + b - 2 * ab), 1 - b, 1 - b + ab, 1 - a, 1 - a + ab, 1 - ab, torch.ones_like(a)]
def mix(a, b, logits, hard, shape):                              # logits (n,16); a, b with a gate axis of size n at dim 1 (n broadcast to shape)
    fs = formulas(a, b)
    if hard: g = logits.argmax(-1); out = torch.zeros_like(a); [out.add_(fs[k] * (g == k).float().view(shape)) for k in range(16)]; return out
    p = torch.softmax(logits, -1); out = 0
    for k in range(16): out = out + fs[k] * p[:, k].view(shape)
    return out
class TreeConv(nn.Module):
    def __init__(self, cin, K, seed):
        super().__init__(); g = torch.Generator().manual_seed(seed); self.K = K
        self.register_buffer("taps", torch.stack([torch.randperm(cin * 9, generator=g)[:8] for _ in range(K)]))
        z = torch.zeros(K, 7, 16); z[:, :, 3] = 5.0; self.logits = nn.Parameter(z)
    def forward(self, x):
        B, C, H, W = x.shape; U = Fn.unfold(Fn.pad(x, (1, 1, 1, 1)), 3).view(B, C * 9, H, W); T = U[:, self.taps]            # (B,K,8,H,W)
        hard = not self.training; sh = (1, self.K, 1, 1)
        l1 = [mix(T[:, :, 2 * j], T[:, :, 2 * j + 1], self.logits[:, j], hard, sh) for j in range(4)]
        l2 = [mix(l1[2 * j], l1[2 * j + 1], self.logits[:, 4 + j], hard, sh) for j in range(2)]
        return mix(l2[0], l2[1], self.logits[:, 6], hard, sh)
class FcGates(nn.Module):
    def __init__(self, nin, nout, seed):
        super().__init__(); g = torch.Generator().manual_seed(seed); perm = torch.cat([torch.randperm(nin, generator=g) for _ in range((2 * nout) // nin + 1)])[:2 * nout]
        self.register_buffer("ia", perm[:nout]); self.register_buffer("ib", perm[nout:]); z = torch.zeros(nout, 16); z[:, 3] = 5.0; self.logits = nn.Parameter(z)
    def forward(self, x): return mix(x[:, self.ia], x[:, self.ib], self.logits, not self.training, (1, -1))
class Net(nn.Module):
    def __init__(self):
        super().__init__(); self.c1 = TreeConv(len(TH), K1, 1); self.c2 = TreeConv(K1, K2, 2); self.f1 = FcGates(K2 * 49, W1, 3); self.f2 = FcGates(W1, W2, 4); self.tau = (W2 // 10) ** 0.5 / 2
    def forward(self, x):
        h = Fn.max_pool2d(self.c1(x), 2); h = Fn.max_pool2d(self.c2(h), 2); h = self.f2(self.f1(h.flatten(1)))
        return (h.view(len(x), 10, -1).sum(2) - W2 / 20) / self.tau
net = Net().to(DEV); opt = torch.optim.Adam(net.parameters(), LR); step = 0; hist = []
if os.path.exists(CK) and not os.environ.get("FRESH"): s = torch.load(CK, map_location=DEV); net.load_state_dict(s["m"]); opt.load_state_dict(s["o"]); step = s["step"]; hist = s["hist"]; print("resumed at step", step, flush=True)
def evaluate(n):
    net.eval()
    with torch.no_grad(): p = torch.cat([net(Ete[i:min(i + 500, n)]).argmax(1) for i in range(0, n, 500)]).cpu().numpy()
    net.train(); return p
def full_report():
    net.eval()
    with torch.no_grad(): sc = torch.cat([net(Ete[i:i + 500]) for i in range(0, 10000, 500)]).cpu().numpy()
    net.train(); p = sc.argmax(1); mk = np.isin(yte, (0, 2, 4, 6)); CL = np.array([0, 2, 4, 6]); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s); tp = np.cumsum(yy[o])
    return "HARD-GATE test accuracy %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f" % ((p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum())
print("gates: conv1 %d x 7, conv2 %d x 7 (shared over positions), fc %d + %d; budget %.0fs" % (K1, K2, W1, W2, BUDGET), flush=True)
net.train(); losses = []
while time.time() - t_start < BUDGET:
    r = np.random.RandomState(step); b = torch.tensor(r.choice(len(Etr), BS, replace=False)).to(DEV); loss = Fn.cross_entropy(net(Etr[b]), Ytr[b]); opt.zero_grad(); loss.backward(); opt.step(); step += 1; losses.append(loss.item())
    if step % 100 == 0:
        a = (evaluate(2000) == yte[:2000]).mean(); hist.append((step, float(np.mean(losses)), float(a))); print("step %d | loss %.3f | hard-gate accuracy on 2,000 test images %.4f | %.0fs" % (step, np.mean(losses), a, time.time() - t_start), flush=True); losses = []
        torch.save({"m": net.state_dict(), "o": opt.state_dict(), "step": step, "hist": hist}, CK)
torch.save({"m": net.state_dict(), "o": opt.state_dict(), "step": step, "hist": hist}, CK); print("saved at step %d" % step + ("; " + full_report() if os.environ.get("REPORT") else ""), flush=True)
