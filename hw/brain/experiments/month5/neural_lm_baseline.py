"""Neural character-model baseline for the counting language model (23 Oct 2026) SIMULATED.
Same text (pydoc topics), same 50/50 split: train on the first half (several epochs), report bits per character on the second half.
Model: embedding of the last 6 characters -> one hidden layer (ReLU) -> 256-way softmax. Memory counted at 8 bits per weight.
The counting model's second-half figures (counting_lm.log) are ONLINE (it learns while reading); this baseline is frozen after training,
so it is not a like-for-like protocol, but it shows what a standard network reaches at the same memory. usage: python neural_lm_baseline.py"""
import math, os, time, torch, torch.nn as nn
import pydoc_data.topics as T
torch.manual_seed(0); torch.set_num_threads(2)
d = torch.tensor(list(open(os.environ["TEXTFILE"], "rb").read() if os.environ.get("TEXTFILE") else "".join(T.topics.values()).encode("utf8", "ignore")), dtype=torch.long)
N = len(d); half = N // 2; C = 6
def ctx(lo, hi):
    idx = torch.arange(lo, hi)
    X = torch.stack([d[(idx - 1 - i).clamp(min=0)] for i in range(C)], 1)
    return X, d[lo:hi]
Xtr, ytr = ctx(0, half); Xte, yte = ctx(half, N)
class M(nn.Module):
    def __init__(s, E, H):
        super().__init__(); s.e = nn.Embedding(256, E); s.f = nn.Linear(C * E, H); s.o = nn.Linear(H, 256)
    def forward(s, x): return s.o(torch.relu(s.f(s.e(x).flatten(1))))
print("| embedding | hidden | weights | memory at 8 bit | bits per char (held-out half) |\n|---|---|---|---|---|")
for E, H in ((8, 32), (16, 128), (16, 512), (32, 1024)):
    m = M(E, H); n = sum(p.numel() for p in m.parameters())
    opt = torch.optim.Adam(m.parameters(), 4e-3); t0 = time.time()
    for ep in range(4):
        perm = torch.randperm(half)
        for i in range(0, half, 2048):
            b = perm[i:i + 2048]; loss = nn.functional.cross_entropy(m(Xtr[b]), ytr[b]); opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad(): bpc = sum(nn.functional.cross_entropy(m(Xte[i:i + 8192]), yte[i:i + 8192], reduction="sum").item() for i in range(0, len(yte), 8192)) / len(yte) / math.log(2)
    print("| %d | %d | %d | %.0f KB | %.3f |  (%.0fs)" % (E, H, n, n / 1024, bpc, time.time() - t0), flush=True)
