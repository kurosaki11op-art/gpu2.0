#!/usr/bin/env python3
"""Striping test S-d: independent count of multiply-adds per decoded token from PyTorch forward hooks (not from the simulator or its analytic rules).
Builds the same shape as gen_decoder.py (default 16 layers, d 512, ff 2048, 4 heads, vocab 8000), decodes token number STEP (0-based) with a cache of STEP earlier tokens, counts Linear multiply-adds with hooks and attention multiply-adds from the tensors passed to torch.matmul via a torch function mode.
usage: torch_count.py [STEP]"""
import sys, torch, torch.nn as nn
from torch.overrides import TorchFunctionMode
D, NL, FF, H, V = 512, 16, 2048, 4, 8000; step = int(sys.argv[1]) if len(sys.argv) > 1 else 0
class Blk(nn.Module):
    def __init__(s):
        super().__init__(); s.q, s.k, s.v, s.o = [nn.Linear(D, D) for _ in range(4)]; s.f1, s.f2 = nn.Linear(D, FF), nn.Linear(FF, D)
        s.mods = nn.ModuleList([s.q, s.k, s.v, s.o, s.f1, s.f2])
    def forward(s, x, kc, vc):
        q, k, v = s.q(x), s.k(x), s.v(x); kc = torch.cat([kc, k], 0); vc = torch.cat([vc, v], 0); t = kc.shape[0]; dh = D // H
        qh = q.view(1, H, dh).transpose(0, 1); kh = kc.view(t, H, dh).transpose(0, 1); vh = vc.view(t, H, dh).transpose(0, 1)
        p = torch.softmax(torch.matmul(qh, kh.transpose(1, 2)) / dh ** 0.5, -1); a = torch.matmul(p, vh).transpose(0, 1).reshape(1, D)
        x = x + s.o(a); return x + s.f2(torch.nn.functional.gelu(s.f1(x))), kc, vc
blocks = nn.ModuleList([Blk() for _ in range(NL)]); head = nn.Linear(D, V); macs = {"linear": 0, "attn": 0}
def hook(m, i, o): macs["linear"] += i[0].numel() // i[0].shape[-1] * m.in_features * m.out_features
for m in list(blocks.modules()) + [head]:
    if isinstance(m, nn.Linear): m.register_forward_hook(hook)
class Cnt(TorchFunctionMode):
    def __torch_function__(self, func, types, args=(), kwargs=None):
        kwargs = kwargs or {}
        if func is torch.matmul: a, b = args[0], args[1]; macs["attn"] += a.shape[0] * a.shape[1] * a.shape[2] * b.shape[2]
        return func(*args, **kwargs)
with torch.no_grad():
    x = torch.randn(1, D); caches = [(torch.zeros(step, D), torch.zeros(step, D)) for _ in range(NL)]
    with Cnt():
        for l, b in enumerate(blocks): x, _, _ = b(x, *caches[l])
        head(x)
print("step", step, "linear", macs["linear"], "attention", macs["attn"], "total", macs["linear"] + macs["attn"])
