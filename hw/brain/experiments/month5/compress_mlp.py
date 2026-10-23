"""Shrinking an existing kind of model without losing accuracy: how far? (23 Oct 2026) SIMULATED, numpy only.
A standard 784-256-128-10 MLP (ReLU, Adam, 12 epochs) on Fashion-MNIST, then: post-training weight quantisation (8 to 2 bits, per-row scale),
magnitude pruning (50 to 95 % zeros) with the zeros stored as an index list, and the entropy of the quantised weights (the lossless limit).
No retraining after shrinking (post-training), then a short fine-tune of 2 epochs with the shrunk weights kept shrunk (quantisation-aware, straight-through).
Reported: test accuracy and storage in KB, against the L Cortex tables on the same data (129 KB, 85.7 % all at once, 81.5 % staged; bits_vs_accuracy.md).
usage: python compress_mlp.py DATA_DIR (Fashion-MNIST idx files named fashion-*)"""
import os, sys, time, gzip
import numpy as np
D = sys.argv[1]
rd = lambda f, o: np.frombuffer(gzip.open(os.path.join(D, "fashion-" + f)).read(), np.uint8, offset=o)
Xtr = rd("train-images-idx3-ubyte.gz", 16).reshape(-1, 784).astype(np.float32) / 255; ytr = rd("train-labels-idx1-ubyte.gz", 8).astype(np.int64)
Xte = rd("t10k-images-idx3-ubyte.gz", 16).reshape(-1, 784).astype(np.float32) / 255; yte = rd("t10k-labels-idx1-ubyte.gz", 8).astype(np.int64)
rs = np.random.RandomState(0); sizes = [784, 256, 128, 10]
W = [rs.randn(a, b).astype(np.float32) * np.sqrt(2.0 / a) for a, b in zip(sizes[:-1], sizes[1:])]; B = [np.zeros(b, np.float32) for b in sizes[1:]]


def fwd(X, W, B, keep=False):
    h = X; acts = [X]
    for i, (w, b) in enumerate(zip(W, B)):
        h = h @ w + b
        if i < len(W) - 1: h = np.maximum(h, 0)
        acts.append(h)
    return acts if keep else h


acc = lambda W, B: float((fwd(Xte, W, B).argmax(1) == yte).mean()) * 100


def train(W, B, epochs, qfun=None, lr=1e-3, seed=0):
    r = np.random.RandomState(seed); m = [np.zeros_like(w) for w in W]; v = [np.zeros_like(w) for w in W]; mb = [np.zeros_like(b) for b in B]; vb = [np.zeros_like(b) for b in B]; t = 0
    for ep in range(epochs):
        perm = r.permutation(len(Xtr))
        for s in range(0, len(Xtr), 256):
            idx = perm[s:s + 256]; X = Xtr[idx]; y = ytr[idx]
            Wq = [qfun(w) for w in W] if qfun else W                       # forward with shrunk weights, gradient applied to the full-precision copy (straight-through)
            acts = fwd(X, Wq, B, keep=True); out = acts[-1]; e = np.exp(out - out.max(1, keepdims=True)); p = e / e.sum(1, keepdims=True)
            g = p; g[np.arange(len(y)), y] -= 1; g /= len(y); t += 1
            for i in range(len(W) - 1, -1, -1):
                gw = acts[i].T @ g; gb = g.sum(0)
                if i > 0: g = (g @ Wq[i].T) * (acts[i] > 0)
                for P, G, M, V in ((W, gw, m, v), (B, gb, mb, vb)):
                    pass
                m[i] = 0.9 * m[i] + 0.1 * gw; v[i] = 0.999 * v[i] + 0.001 * gw * gw; W[i] -= lr * (m[i] / (1 - 0.9 ** t)) / (np.sqrt(v[i] / (1 - 0.999 ** t)) + 1e-8)
                mb[i] = 0.9 * mb[i] + 0.1 * gb; vb[i] = 0.999 * vb[i] + 0.001 * gb * gb; B[i] -= lr * (mb[i] / (1 - 0.9 ** t)) / (np.sqrt(vb[i] / (1 - 0.999 ** t)) + 1e-8)
    return W, B


def quant(w, bits):
    if bits >= 16: return w
    q = (1 << (bits - 1)) - 1; s = np.abs(w).max(0, keepdims=True) / q + 1e-12
    return np.clip(np.round(w / s), -q, q) * s


def ent_bits(w, bits):
    q = (1 << (bits - 1)) - 1; s = np.abs(w).max(0, keepdims=True) / q + 1e-12; c = np.clip(np.round(w / s), -q, q).astype(np.int64).ravel()
    p = np.bincount(c + q) / len(c); p = p[p > 0]; return float(-(p * np.log2(p)).sum())


def prune(w, frac):
    t = np.quantile(np.abs(w), frac); return np.where(np.abs(w) >= t, w, 0)


t0 = time.time(); W, B = train(W, B, 12); nparam = sum(w.size for w in W)
base = acc(W, B); print("float32 MLP: %d weights, %.1f KB, test accuracy %.2f %%  (%.0fs)" % (nparam, nparam * 4 / 1024, base, time.time() - t0), flush=True)
W3, B3 = train([w.copy() for w in W], [b.copy() for b in B], 2, lr=2e-4); base_ft = acc(W3, B3)
print("float32 + the same 2 extra epochs: %.2f %% (the fair baseline for the fine-tuned rows)" % base_ft, flush=True)
print("\n| shrink | storage KB | accuracy after shrinking | after a 2-epoch fine-tune | fine-tuned change vs float + 2 epochs |"); print("|---|---|---|---|---|")
for bits in (8, 6, 5, 4, 3, 2):
    a0 = acc([quant(w, bits) for w in W], B)
    W2, B2 = train([w.copy() for w in W], [b.copy() for b in B], 2, qfun=lambda w, b=bits: quant(w, b), lr=2e-4); a1 = acc([quant(w, bits) for w in W2], B2)
    kb = nparam * bits / 8 / 1024; ekb = sum(w.size * ent_bits(w, bits) for w in W) / 8 / 1024
    print("| %d-bit weights | %.1f (entropy limit %.1f) | %.2f | %.2f | %+.2f |" % (bits, kb, ekb, a0, a1, a1 - base_ft), flush=True)
for frac in (0.5, 0.7, 0.8, 0.9, 0.95):
    Wp = [prune(w, frac) for w in W]; a0 = acc(Wp, B)
    nz = sum(int((w != 0).sum()) for w in Wp); kb = nz * (8 + 11) / 8 / 1024                    # 8-bit value + about 11-bit index per kept weight
    print("| prune %d %% (8-bit values + index) | %.1f | %.2f | - | %+.2f |" % (100 * frac, kb, a0, a0 - base), flush=True)
print("\nL Cortex on the same data (integer model, tables 129 KB): 85.7 %% all at once, 81.5 %% in stages; a float MLP reaches %.1f %% (this run)." % base)
