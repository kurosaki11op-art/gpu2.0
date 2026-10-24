"""Convolutional lookup-table network (accelerator path), 24 Oct 2026. SIMULATED/MEASURED on CPU, torch.
Inference uses ONLY table lookups, ORs (max-pool) and popcounts: no multiply, no matrix, no float.
Layer 1: F1 shared LUT filters; each filter reads n bits (random taps of a 3x3 window over the thermometer-coded picture) as a table index, slides over the picture.
Max-pool 2x2 (OR). Layer 2: F2 shared LUT filters over the F1 maps, same scheme, max-pool. Output: 10 x N LUTs reading n random bits of the flattened maps; class score = popcount of its group.
Training (GPU or CPU, not on the chip): table entries are real numbers, the bit is their sign; gradients through hard bits with a straight-through rule and the finite-difference rule
of weightless nets (d value / d input bit = table[index with bit=1] - table[index with bit=0]). Deployed as 1-bit tables.
usage: python conv_lut.py DATA_DIR [epochs] ; checkpoints to conv_lut_ckpt.pt after every epoch (resumable)."""
import sys, os, gzip, time, numpy as np, torch, torch.nn as nn
torch.set_num_threads(4); D = sys.argv[1]; EPOCHS = int(sys.argv[2]) if len(sys.argv) > 2 else 6
F1, F2, N, n = int(os.environ.get("F1", 32)), int(os.environ.get("F2", 64)), int(os.environ.get("NOUT", 300)), int(os.environ.get("NIN", 6))
rd = lambda f, o: np.frombuffer(gzip.open(os.path.join(D, "fashion-" + f)).read(), np.uint8, offset=o)
Xtr = rd("train-images-idx3-ubyte.gz", 16).reshape(-1, 28, 28); ytr = rd("train-labels-idx1-ubyte.gz", 8).astype(np.int64)
Xte = rd("t10k-images-idx3-ubyte.gz", 16).reshape(-1, 28, 28); yte = rd("t10k-labels-idx1-ubyte.gz", 8).astype(np.int64)
TH = (40, 100, 160, 220)
enc = lambda x: torch.tensor(np.stack([(x > t) for t in TH], 1).astype(np.float32))          # (B, 4, 28, 28) thermometer bits
Etr, Ete = enc(Xtr), enc(Xte); Ytr = torch.tensor(ytr)
pw = (2 ** torch.arange(n)).long()
class LutFn(torch.autograd.Function):
    @staticmethod
    def forward(ctx, xs, Wt):                     # xs (B,P,F,n) bits as float; Wt (2^n, F) table values
        idx = (xs.long() * pw).sum(-1); F = Wt.shape[1]; v = Wt[idx, torch.arange(F)]
        ctx.save_for_backward(idx, Wt); return v
    @staticmethod
    def backward(ctx, gv):
        idx, Wt = ctx.saved_tensors; F = Wt.shape[1]; ar = torch.arange(F)
        gW = torch.zeros_like(Wt); gW.index_put_((idx, ar.expand_as(idx)), gv, accumulate=True)
        gx = torch.stack([gv * (Wt[idx | (1 << j), ar] - Wt[idx & ~(1 << j), ar]) for j in range(n)], -1)
        return gx, gW
def hard(v): return (v > 0).float() + (torch.clamp(v, -1, 1) - torch.clamp(v, -1, 1).detach())     # forward: bit; backward: straight-through inside |v| < 1
class ConvLut(nn.Module):
    def __init__(self, cin, F, seed):
        super().__init__(); g = torch.Generator().manual_seed(seed); self.F = F
        self.taps = torch.stack([torch.randperm(cin * 9, generator=g)[:n] for _ in range(F)])          # (F, n) taps into (channel, 3x3 window)
        self.W = nn.Parameter(torch.randn(2 ** n, F, generator=g) * 0.1)
    def forward(self, x):                          # x (B,C,H,W) bits
        B, C, H, Wd = x.shape; u = nn.functional.pad(x, (1, 1, 1, 1)).unfold(2, 3, 1).unfold(3, 3, 1)       # (B,C,H,W,3,3)
        u = u.permute(0, 2, 3, 1, 4, 5).reshape(B, H * Wd, C * 9); xs = u[:, :, self.taps]                   # (B,P,F,n)
        v = LutFn.apply(xs, self.W); return hard(v).view(B, H, Wd, self.F).permute(0, 3, 1, 2)
class Net(nn.Module):
    def __init__(self):
        super().__init__(); self.l1 = ConvLut(len(TH), F1, 1); self.l2 = ConvLut(F1, F2, 2); L = 10 * N
        self.taps = torch.randint(0, F2 * 49, (L, n), generator=torch.Generator().manual_seed(3)); self.W = nn.Parameter(torch.randn(2 ** n, L) * 0.1)
        self.pool = nn.MaxPool2d(2)
    def forward(self, x):
        h = self.pool(self.l1(x)); h = self.pool(self.l2(h)); flat = h.flatten(1); xs = flat[:, self.taps].unsqueeze(1)   # (B,1,L,n)
        o = hard(LutFn.apply(xs, self.W)).squeeze(1); return o.view(len(x), 10, N).sum(2)
net = Net(); opt = torch.optim.Adam(net.parameters(), 0.02); ck = "conv_lut_ckpt.pt"; ep0 = 0
if os.path.exists(ck) and not os.environ.get("FRESH"): s = torch.load(ck); net.load_state_dict(s["m"]); opt.load_state_dict(s["o"]); ep0 = s["ep"]; print("resumed from epoch", ep0, flush=True)
def evaluate():
    with torch.no_grad(): p = torch.cat([net(Ete[i:i + 500]).argmax(1) for i in range(0, len(Ete), 500)]).numpy()
    return (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[yte == 0] == 0).mean(), (p[yte == 2] == 2).mean(), (p[yte == 4] == 4).mean()
print("deployed tables: %.1f KB (1 bit per entry)" % ((F1 + F2) * 2 ** n / 8 / 1024 + 10 * N * 2 ** n / 8 / 1024), flush=True)
t0 = time.time(); BS = 64
for ep in range(ep0, EPOCHS):
    perm = torch.randperm(len(Etr)); tl = 0; steps = 0
    for i in range(0, len(Etr), BS):
        b = perm[i:i + BS]; loss = nn.functional.cross_entropy((net(Etr[b]) - N / 2) * (4.0 / np.sqrt(N)), Ytr[b]); opt.zero_grad(); loss.backward(); opt.step(); tl += loss.item(); steps += 1
        if os.environ.get("BENCH") and steps == 20: print("20 steps %.1fs" % (time.time() - t0), flush=True); sys.exit()
    a = evaluate(); print("epoch %d | train loss %.3f | test accuracy %.4f | Shirt %.3f T-shirt %.3f Pullover %.3f Coat %.3f | %.0fs" % (ep + 1, tl / steps, *a, time.time() - t0), flush=True)
    torch.save({"m": net.state_dict(), "o": opt.state_dict(), "ep": ep + 1}, ck)
