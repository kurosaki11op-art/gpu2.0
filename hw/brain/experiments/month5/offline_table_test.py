"""28 Oct 2026, SIMULATED. Same inference hardware (a 4,608 x 10 int8 table read by the active code bits, adds only), but the table is trained OFFLINE with a proper rule (softmax regression, Adam; host or GPU training, as the accelerator rule says) instead of the chip's on-line counting rule, then rounded to int8.
Question: how much of the gap to a CNN is the table's learning rule, not the code? Compares: on-chip rule (shipped CortexSlow table), offline softmax float, offline int8 (scale to +-127), with and without the flipped training copies. Inference cost is identical (table size and adds unchanged)."""
import sys, time
sys.argv = ["x", "/tmp/fashion"]
sys.path.insert(0, "/home/user/gpu2.0/hw/brain/experiments/month5")
import numpy as np, torch
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table
torch.manual_seed(0); torch.set_num_threads(4); t0 = time.time()
def fit(X, y, epochs=40, lr=0.02, wd=0.0, bs=512):
    Xt = torch.tensor(X, dtype=torch.float32); yt = torch.tensor(y); W = torch.zeros(X.shape[1], 10, requires_grad=True); b = torch.zeros(10, requires_grad=True); opt = torch.optim.Adam([W, b], lr=lr, weight_decay=wd)
    for ep in range(epochs):
        perm = torch.randperm(len(yt))
        for i in range(0, len(yt), bs):
            ix = perm[i:i + bs]; opt.zero_grad(); loss = torch.nn.functional.cross_entropy(Xt[ix] @ W + b, yt[ix]); loss.backward(); opt.step()
    return W.detach().numpy(), b.detach().numpy()
def int8(W, b):
    s = 127.0 / np.abs(W).max(); return np.round(W * s).astype(np.int32), np.round(b * s).astype(np.int32)
def acc(Wi, bi): S = cte.astype(np.int32) @ Wi + bi; return (S.argmax(1) == yte).mean()
print("on-chip rule (shipped table): %.4f" % ((cte.astype(np.int32) @ train_table(ctr, ytr)).argmax(1) == yte).mean(), flush=True)
for tag, wd in (("no decay", 0.0), ("weight decay 1e-5", 1e-5)):
    W, b = fit(ctr, ytr, wd=wd); fl = ((cte.astype(np.float32) @ W + b).argmax(1) == yte).mean(); Wi, bi = int8(W, b)
    print("offline softmax, %-18s float %.4f | int8 table + bias %.4f | int8 range %d..%d [%.0fs]" % (tag, fl, acc(Wi, bi), Wi.min(), Wi.max(), time.time() - t0), flush=True)
