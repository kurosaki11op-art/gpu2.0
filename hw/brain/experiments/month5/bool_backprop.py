"""24 Oct 2026, SIMULATED, MNIST digits, one seed. Can a gate network learn with an error signal that needs no multiplies and no matrices?
Same network for all arms: input = 2 thresholds per pixel (1,568 bits), gate layers [N1, N2, 1000] (each gate: 2 inputs at fixed random wiring, 16 possible truth tables), output = popcount of 10 groups of 100 bits.
ARM=float    : relaxed gates (softmax over 16 truth tables), real-valued backprop, Adam. Reference only (the yardstick, not the design).
ARM=signgrad : same relaxed forward, but the error handed back across every layer is reduced to its sign (-1, 0, +1).
ARM=integer  : hard gates only. The error is a value in {-1,0,+1} per node. Backward through a gate = lookup of its Boolean derivative in the truth table; a node's error = sign of the sum of the wishes of the nodes it feeds. Each gate keeps 16 integer counters (one per truth table): +1 if that truth table would have given the wanted output on this input, -1 if not; the gate is the largest counter. Only adds, compares, lookups, counters.
env: ARM, EPOCHS, N1, N2, BATCH, LR, MARGIN, CMAX. usage: python3 bool_backprop.py"""
import os, sys, time
import numpy as np
ARM = os.environ.get("ARM", "integer"); EPOCHS = int(os.environ.get("EPOCHS", 3)); N1 = int(os.environ.get("N1", 2000)); N2 = int(os.environ.get("N2", 2000)); BATCH = int(os.environ.get("BATCH", 64))
LR = float(os.environ.get("LR", 0.05)); MARGIN = int(os.environ.get("MARGIN", 10)); CMAX = int(os.environ.get("CMAX", 1000000)); G = 100; SEED = int(os.environ.get("SEED", 0))
rs = np.random.RandomState(SEED)
z = np.load(os.environ.get("MNIST", "/tmp/mnistdata/mnist.npz")); xtr = z["x_train"].reshape(-1, 784); ytr = z["y_train"].astype(np.int64); xte = z["x_test"].reshape(-1, 784); yte = z["y_test"].astype(np.int64)
bits = lambda x: np.concatenate([x > 85, x > 170], 1).astype(np.uint8); Xtr, Xte = bits(xtr), bits(xte)
sizes = [Xtr.shape[1], N1, N2, 10 * G]
wiring = [(rs.randint(0, sizes[i], sizes[i + 1]), rs.randint(0, sizes[i], sizes[i + 1])) for i in range(3)]
BIT = np.array([[(g >> (2 * a + b)) & 1 for b in (0, 1) for a in (0, 1)] for g in range(16)])        # unused ordering helper (kept simple below)
TT = np.array([[[(g >> (2 * a + b)) & 1 for b in (0, 1)] for a in (0, 1)] for g in range(16)], np.int8)   # TT[g][a][b]; gate 12 = pass input A, gate 10 = pass input B
t0 = time.time()

def accuracy(pred, y): return (pred == y).mean()

if ARM == "integer":
    C = [np.zeros((sizes[i + 1], 16), np.int32) for i in range(3)]
    for c in C: c[:, 12] = 3                                                                              # start as pass-through (residual start)
    gate = lambda i: C[i].argmax(1)
    def forward(X, layers=True):
        acts = [X.astype(np.int8)]
        for i in range(3):
            g = gate(i); a = acts[-1][:, wiring[i][0]]; b = acts[-1][:, wiring[i][1]]; acts.append(TT[g[None, :], a, b])
        return acts
    def scores(acts): return acts[-1].reshape(len(acts[-1]), 10, G).sum(2)
    def evaluate(X, y):
        s = np.concatenate([scores(forward(X[i:i + 5000])) for i in range(0, len(X), 5000)]); return accuracy(s.argmax(1), y)
    tab = (2 * TT.astype(np.int32) - 1)                                                                  # +1 if the truth table outputs 1 here, -1 if 0
    for ep in range(EPOCHS):
        perm = rs.permutation(len(Xtr)); changed = 0
        for k in range(0, len(perm) - BATCH + 1, BATCH):
            idx = perm[k:k + BATCH]; acts = forward(Xtr[idx]); s = scores(acts); y = ytr[idx]
            order = np.argsort(-s, 1); top = np.where(order[:, 0] == y, order[:, 1], order[:, 0]); n = np.arange(BATCH)
            need = (s[n, y] - s[n, top]) < MARGIN                                                          # wrong, or right with a small margin
            e = np.zeros((BATCH, 10 * G), np.int8); gi = np.arange(10 * G).reshape(10, G)
            if os.environ.get("OUT", "ova") == "ova":                                                      # one-vs-rest target per output bit: on for the true class's group, off for the others (positives weighted 9:1 to balance)
                tgt = (np.repeat(np.arange(10), G)[None, :] == y[:, None]); e = np.where(tgt, 9, -1).astype(np.int8)
            else:
                for r in np.where(need)[0]:
                    e[r, gi[y[r]]] = 1; e[r, gi[top[r]]] = -1
            e_count = e.copy() if os.environ.get("COUNT", "all") == "all" else None                          # output layer counts every example (best gate = most correlated with the class); errors are passed down only where a bit disagrees
            out = acts[3]; e[(e > 0) & (out == 1)] = 0; e[(e < 0) & (out == 0)] = 0                      # nothing to change where the bit already agrees
            for i in (2, 1, 0):
                ia, ib = wiring[i]; a = acts[i][:, ia]; b = acts[i][:, ib]; wanted = np.where(e > 0, 1, 0)
                # counters: +e for truth tables that give 1 here, -e for those that give 0 (only where e != 0)
                C[i] = np.clip(C[i] + np.einsum("nj,njg->jg", (e_count if (i == 2 and e_count is not None) else e).astype(np.int32), tab[:, a, b].transpose(1, 2, 0) if False else tab[np.arange(16)[None, None, :], a[:, :, None], b[:, :, None]]), -CMAX, CMAX).astype(np.int32)
                if i == 0: break
                g = gate(i); dA = TT[g[None, :], 1, b] - TT[g[None, :], 0, b]; dB = TT[g[None, :], a, 1] - TT[g[None, :], a, 0]       # Boolean derivatives by lookup
                n_prev = sizes[i]; flat = (np.arange(BATCH)[:, None] * n_prev)
                err = np.bincount((flat + ia[None, :]).ravel(), weights=(e * dA).ravel(), minlength=BATCH * n_prev) + np.bincount((flat + ib[None, :]).ravel(), weights=(e * dB).ravel(), minlength=BATCH * n_prev)
                ep_ = np.sign(err).reshape(BATCH, n_prev).astype(np.int8); prev = acts[i]; ep_[(ep_ > 0) & (prev == 1)] = 0; ep_[(ep_ < 0) & (prev == 0)] = 0; e = ep_
        print("integer arm epoch %d: train-batch need %.2f | test acc %.4f | %.0fs" % (ep + 1, need.mean(), evaluate(Xte, yte), time.time() - t0), flush=True)
else:
    import torch, torch.nn as nn
    torch.manual_seed(SEED); torch.set_num_threads(4); BT = torch.tensor([[(g >> p) & 1 for p in range(4)] for g in range(16)], dtype=torch.float32)   # pattern order: p = 2a+b
    class SignGrad(torch.autograd.Function):
        @staticmethod
        def forward(ctx, x): return x.view_as(x)
        @staticmethod
        def backward(ctx, g):
            th = float(os.environ.get("TERN", 0)) * g.abs().mean(1, keepdim=True)                         # ternary: errors below TERN x the mean magnitude of the example become 0
            return torch.sign(g) * (g.abs() >= th)
    class QGrad(torch.autograd.Function):                                                                   # error handed back as a small integer in [-levels, levels]; errors under tern x the example's mean magnitude become 0
        @staticmethod
        def forward(ctx, x, levels, tern): ctx.lv, ctx.tn = levels, tern; return x.view_as(x)
        @staticmethod
        def backward(ctx, g):
            m = (g.abs().max() if os.environ.get("PB", "0") == "1" else g.abs().amax(1, keepdim=True)) + 1e-12; q = torch.round(g / m * ctx.lv); q = q * (g.abs() >= ctx.tn * g.abs().mean(1, keepdim=True)); return q, None, None
    L = [nn.Parameter(torch.zeros(sizes[i + 1], 16)) for i in range(3)]
    for l in L: l.data[:, 12] = 5.0
    W = [(torch.tensor(a), torch.tensor(b)) for a, b in wiring]
    def fwd(x, hard):
        for i in range(3):
            a = x[:, W[i][0]]; b = x[:, W[i][1]]
            if hard:
                g = L[i].argmax(1); x = BT[g][:, :].gather(1, (2 * a.long() + b.long()).T).T if False else torch.stack([BT[g[j]][(2 * a[:, j].long() + b[:, j].long())] for j in range(0)], 1) if False else (BT[g][None, :, :].expand(len(x), -1, -1).gather(2, (2 * a.long() + b.long())[:, :, None]))[:, :, 0]
            else:
                P = torch.stack([(1 - a) * (1 - b), (1 - a) * b, a * (1 - b), a * b], 2); pg = torch.softmax(L[i], 1); x = (P * (pg @ BT)[None]).sum(2)
                if ARM == "qgrad": x = QGrad.apply(x, int(os.environ.get("OL", 7)) if i == 2 else int(os.environ.get("HL", 1)), float(os.environ.get("TERN", 1)) if i < 2 else 0.0)
                if ARM == "signgrad" and (i < 2 or os.environ.get("SIGNOUT", "1") == "1"): x = SignGrad.apply(x)
        return x
    opt = torch.optim.Adam(L, LR); TAU = 10.0; Xt = torch.tensor(Xtr, dtype=torch.float32); Yt = torch.tensor(ytr); Xe = torch.tensor(Xte, dtype=torch.float32)
    def evaluate():
        with torch.no_grad(): s = torch.cat([fwd(Xe[i:i + 1000], True).reshape(-1, 10, G).sum(2) for i in range(0, len(Xe), 1000)]); return (s.argmax(1).numpy() == yte).mean()
    for ep in range(EPOCHS):
        pm = torch.randperm(len(Xt))
        for k in range(0, len(pm) - BATCH + 1, BATCH):
            b = pm[k:k + BATCH]; s = fwd(Xt[b], False).reshape(BATCH, 10, G).sum(2) / TAU; loss = nn.functional.cross_entropy(s, Yt[b]); opt.zero_grad(); loss.backward()
            if os.environ.get("UPD", "adam") == "sign":                                                         # integer counters: every step adds or subtracts STEP to a gate's 16 counters (no real-valued optimiser state)
                with torch.no_grad():
                    for l in L: l -= float(os.environ.get("STEP", 1)) * torch.sign(l.grad); l.clamp_(-float(os.environ.get("LCLAMP", 30)), float(os.environ.get("LCLAMP", 30))); l.round_()
            else: opt.step()
        print("%s arm epoch %d: test acc (hard gates) %.4f | %.0fs" % (ARM, ep + 1, evaluate(), time.time() - t0), flush=True)
