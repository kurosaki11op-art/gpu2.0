"""25 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed. Two brains: fast brain = L's counting table (about 590 row reads); slow brain = a learned hidden layer on L's code (1,024 binary units, pruned to FAN connections per unit, 4-bit weights; trained by backprop on a host as a stand-in for the integer learner), consulted ONLY when the fast brain's margin (top1 - top2) is small.
Protocol: both brains trained on 50,000 training images; the escalation threshold is chosen on the last 10,000 training images so that a fraction Q of images is escalated; results on the 10,000 test images. Cost model: mean adds per image = 590 + Q x slow-brain adds (event-driven: active input bits x connections per input bit).
Final score of an image: escalated images use the slow brain's scores, others the fast table's (both scaled to unit spread); Shirt AP is computed on these final scores (approximation, stated).
env: FAN (default 256), H (1024)"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, CL
import torch, torch.nn as nn
FAN, H = int(os.environ.get("FAN", 256)), int(os.environ.get("H", 1024)); ntr = 50000; t0 = time.time(); torch.manual_seed(0); torch.set_num_threads(4)
W0 = train_table(ctr[:ntr], ytr[:ntr]); Sv = ctr[ntr:].astype(np.int32) @ W0; St = cte.astype(np.int32) @ W0; yv = ytr[ntr:]; print("[%3.0fs] fast brain trained: validation %.4f test %.4f" % (time.time() - t0, (Sv.argmax(1) == yv).mean(), (St.argmax(1) == yte).mean()), flush=True)
class SignSTE(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x): ctx.save_for_backward(x); return (x > 0).float()
    @staticmethod
    def backward(ctx, g): (x,) = ctx.saved_tensors; return g * (x.abs() < 1).float()
def quant(w, bits):
    q = (1 << (bits - 1)) - 1; sc = w.abs().max(1, keepdim=True).values / q + 1e-12; return torch.round(w / sc).clamp(-q, q) * sc
Xu = torch.tensor(ctr[:ntr]); Y = torch.tensor(ytr[:ntr]); l1 = nn.Linear(4608, H); l2 = nn.Linear(H, 10); opt = torch.optim.Adam(list(l1.parameters()) + list(l2.parameters()), 1e-3)
def train(ep, mask):
    for _ in range(ep):
        pm = torch.randperm(ntr)
        for i in range(0, ntr, 256):
            b = pm[i:i + 256]; w = l1.weight if mask is None else l1.weight * mask; loss = nn.functional.cross_entropy(l2(SignSTE.apply(Xu[b].float() @ w.T + l1.bias)), Y[b]); opt.zero_grad(); loss.backward(); opt.step()
train(8, None); print("[%3.0fs] slow brain dense trained" % (time.time() - t0), flush=True)
imp = l1.weight.abs() * Xu[:5000].float().mean(0)[None, :]; idx = imp.topk(FAN, dim=1).indices; mask = torch.zeros_like(l1.weight); mask.scatter_(1, idx, 1.0)
opt = torch.optim.Adam(list(l1.parameters()) + list(l2.parameters()), 5e-4); train(4, mask)
with torch.no_grad():
    w1 = quant(l1.weight * mask, 4); w2 = quant(l2.weight, 8)
    def slow(C): return np.concatenate([(((torch.tensor(C[i:i + 2000]).float() @ w1.T + l1.bias) > 0).float() @ w2.T + l2.bias).numpy() for i in range(0, len(C), 2000)])
    Tv, Tt = slow(ctr[ntr:]), slow(cte)
adds = float(ctr[:2000].sum(1).mean()) * H * FAN / 4608; print("[%3.0fs] slow brain pruned to fan-in %d: validation %.4f test %.4f; adds per image if always used: %.0f (fast brain: %.0f row reads)" % (time.time() - t0, FAN, (Tv.argmax(1) == yv).mean(), (Tt.argmax(1) == yte).mean(), adds, ctr[:2000].sum(1).mean()), flush=True)
def z(S): return (S - S.mean(1, keepdims=True)) / (S.std() + 1e-9)
def metrics(sc):
    p = sc.argmax(1); mk = np.isin(yte, CL); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    return (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap
def marg(S): s = np.sort(S, 1); return s[:, -1] - s[:, -2]
print("%-34s acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | mean adds %5.0f (x%.1f of L)" % (("fast brain alone",) + metrics(St) + (ctr[:2000].sum(1).mean(), 1.0)))
print("%-34s acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | mean adds %5.0f (x%.1f of L)" % (("slow brain alone",) + metrics(Tt) + (adds, adds / ctr[:2000].sum(1).mean())))
mv, mt = marg(Sv), marg(St)
for Q in (0.05, 0.10, 0.20, 0.40):
    thr = np.quantile(mv, Q); esc = mt <= thr; final = np.where(esc[:, None], z(Tt), z(St)); base = ctr[:2000].sum(1).mean(); cost = base + esc.mean() * adds
    print("%-34s acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | mean adds %5.0f (x%.1f of L) | escalated %.1f%%" % (("escalate lowest-margin %d%%" % (Q * 100),) + metrics(final) + (cost, cost / base, esc.mean() * 100)))
