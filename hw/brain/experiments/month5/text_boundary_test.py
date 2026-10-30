"""30 Oct 2026, SIMULATED (quality), ESTIMATED (energy). BOUNDARY TEST: do L's methods (counting tables, hashed lookups, adds) carry over from images to language? Character-level next-character prediction on Tiny Shakespeare (1,115,394 characters; last 10% held out), scored in bits per character (BPC, lower is better; 6.02 = random over 65 symbols).
(1) counting-table model: interpolated n-gram with absolute discounting, orders 1 to 8 (counts and table reads, no matrices, no training by gradient, learns in ONE pass over the text);
(2) reference transformer (2 layers, d=128, context 128) trained by gradient descent on this CPU for a fixed time budget, so UNDERTRAINED: a floor for what a transformer gets, not its best.
Energy per predicted character from operation counts only (ESTIMATED): table reads at 10 pJ per 64-bit word (project constant, small SRAM) per order; transformer multiply-adds at 0.2 pJ."""
import math, os, sys, time
from collections import defaultdict
import numpy as np
P = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/text/shakespeare.txt"
txt = open(P).read(); chars = sorted(set(txt)); V = len(chars); idx = {c: i for i, c in enumerate(chars)}; data = np.array([idx[c] for c in txt], np.int32); cut = int(0.9 * len(data)); tr, te = data[:cut], data[cut:]
print("vocabulary %d, train %d chars, test %d chars" % (V, len(tr), len(te)), flush=True); t0 = time.time()
# ---- (1) interpolated absolute-discounting n-gram, orders 1..N
N = 8; D = 0.75; tabs = [defaultdict(lambda: defaultdict(int)) for _ in range(N + 1)]
trl = tr.tolist()
for i in range(len(trl)):
    for k in range(0, N + 1):                         # context length k (k = 0 is the unigram table)
        if i - k < 0: break
        tabs[k][tuple(trl[i - k:i])][trl[i]] += 1
tot = [{c: (sum(d.values()), len(d)) for c, d in t.items()} for t in tabs]
def prob(ctx, c, kmax):
    p = 1.0 / V
    for k in range(0, kmax + 1):
        key = tuple(ctx[len(ctx) - k:]) if k else ()
        if len(ctx) < k or key not in tot[k]: break
        n, ty = tot[k][key]; cnt = tabs[k][key].get(c, 0); p = max(cnt - D, 0) / n + (D * ty / n) * p
    return p
tel = te.tolist(); print("[%3.0fs] n-gram tables built (one pass over the training text)" % (time.time() - t0), flush=True)
nent = [sum(len(d) for d in t.values()) for t in tabs]
for kmax in (0, 1, 2, 3, 4, 5, 6, 7, 8):
    bits = 0.0; M = 40000
    for i in range(M): bits -= math.log2(prob(tel[max(0, i - kmax):i], tel[i], kmax))
    kb = sum(nent[:kmax + 1]) * 2 / 1024    # about 2 bytes per stored (context, symbol) count (generous: a real table packs less)
    print("n-gram order %d: %.3f BPC | stored counts %d (about %.0f KB at 2 bytes) | table reads per character %d | [%3.0fs]" % (kmax + 1, bits / M, sum(nent[:kmax + 1]), kb, kmax + 1, time.time() - t0), flush=True)
# ---- (2) reference transformer, CPU, fixed time budget
import torch, torch.nn as nn
torch.manual_seed(0); torch.set_num_threads(3); BUD = float(os.environ.get("BUDGET", 600)); CT = 128; dm = 128
class Blk(nn.Module):
    def __init__(s): super().__init__(); s.l1 = nn.LayerNorm(dm); s.at = nn.MultiheadAttention(dm, 4, batch_first=True); s.l2 = nn.LayerNorm(dm); s.ff = nn.Sequential(nn.Linear(dm, 4 * dm), nn.GELU(), nn.Linear(4 * dm, dm))
    def forward(s, x, m): h = s.l1(x); x = x + s.at(h, h, h, attn_mask=m, need_weights=False)[0]; return x + s.ff(s.l2(x))
class TL(nn.Module):
    def __init__(s): super().__init__(); s.e = nn.Embedding(V, dm); s.p = nn.Parameter(torch.zeros(CT, dm)); s.b = nn.ModuleList([Blk(), Blk()]); s.n = nn.LayerNorm(dm); s.o = nn.Linear(dm, V)
    def forward(s, x):
        m = torch.triu(torch.ones(x.shape[1], x.shape[1], dtype=torch.bool), 1); h = s.e(x) + s.p[: x.shape[1]]
        for b in s.b: h = b(h, m)
        return s.o(s.n(h))
net = TL(); npar = sum(p.numel() for p in net.parameters()); opt = torch.optim.AdamW(net.parameters(), lr=3e-3, weight_decay=0.01); trt = torch.tensor(tr, dtype=torch.long); tet = torch.tensor(te, dtype=torch.long)
def batch(src, bs):
    ix = torch.randint(0, len(src) - CT - 1, (bs,)); return torch.stack([src[i:i + CT] for i in ix]), torch.stack([src[i + 1:i + CT + 1] for i in ix])
def evaluate():
    net.eval(); tot_, n_ = 0.0, 0
    with torch.no_grad():
        for s in range(0, 40000, CT):
            x = tet[s:s + CT][None]; y = tet[s + 1:s + CT + 1][None]
            if x.shape[1] < CT or y.shape[1] < CT: break
            tot_ += nn.functional.cross_entropy(net(x)[0], y[0], reduction="sum").item(); n_ += CT
    net.train(); return tot_ / n_ / math.log(2)
t1 = time.time(); step = 0
while time.time() - t1 < BUD:
    x, y = batch(trt, 32); opt.zero_grad(); nn.functional.cross_entropy(net(x).reshape(-1, V), y.reshape(-1)).backward(); opt.step(); step += 1
    if step % 300 == 0: print("  transformer step %d (%.0fs): held-out %.3f BPC" % (step, time.time() - t1, evaluate()), flush=True)
b = evaluate(); macs = 2 * (12 * dm * dm + dm * V) // 1 + 2 * CT * dm * 2    # per token: 2 layers x (4 d^2 attention + 8 d^2 MLP) + output layer + attention scores (rough)
print("reference transformer (2 layers, d=128, context 128, %d parameters, %d steps, %.0f s on this CPU, undertrained): %.3f BPC" % (npar, step, BUD, b))
print("ESTIMATED energy per character: transformer about %.2f M multiply-adds = %.2f uJ (multiplies only); 8-order counting table: 8 reads = %.3f uJ" % (macs / 1e6, macs * 0.2e-6, 8 * 10e-6 / 1))
