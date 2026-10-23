"""Staged-learning (forgetting) test of the standard MLP and its 4-bit version (23 Oct 2026) SIMULATED, numpy only. Same protocol as the L Cortex staged test: 5 stages of 2 classes (2,000 images per stage), no stored examples, 3 epochs per stage; test on all classes after the last stage. Original docstring of compress_mlp.py follows.
Shrinking an existing kind of model without losing accuracy: how far? (23 Oct 2026) SIMULATED, numpy only.
A standard 784-256-128-10 MLP (ReLU, Adam, 12 epochs) on Fashion-MNIST, then: post-training weight quantisation (8 to 2 bits, per-row scale),
magnitude pruning (50 to 95 % zeros) with the zeros stored as an index list, and the entropy of the quantised weights (the lossless limit).
No retraining after shrinking (post-training), then a short fine-tune of 2 epochs with the shrunk weights kept shrunk (quantisation-aware, straight-through).
Reported: test accuracy and storage in KB, against the L Cortex tables on the same data (129 KB, 85.7 % all at once, 81.5 % staged; bits_vs_accuracy.md).
usage: python compress_mlp.py DATA_DIR (Fashion-MNIST idx files named fashion-*)"""
import os, sys, time, gzip
import numpy as np
D = sys.argv[1]; DSN = os.environ.get("DS", "fashion"); PREFIX = "fashion-" if DSN == "fashion" else ""
rd = lambda f, o: np.frombuffer(gzip.open(os.path.join(D, PREFIX + f)).read(), np.uint8, offset=o)
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



STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; NPS = 2000


def run(bits, seed):
    r = np.random.RandomState(seed); W = [r.randn(a, b).astype(np.float32) * np.sqrt(2.0 / a) for a, b in zip(sizes[:-1], sizes[1:])]; B = [np.zeros(b, np.float32) for b in sizes[1:]]
    global Xtr, ytr
    X0, y0 = Xtr, ytr; qf = (lambda w: quant(w, bits)) if bits < 16 else None
    first_acc = []
    for st in STAGES:
        idx = np.concatenate([r.permutation(np.where(y0 == c)[0])[:NPS // 2] for c in st]); Xtr, ytr = X0[idx], y0[idx]
        W, B = train(W, B, 3, qfun=qf, seed=seed)
        Wq = [quant(w, bits) for w in W] if bits < 16 else W; first_acc.append(acc(Wq, B))
    Xtr, ytr = X0, y0
    return first_acc


for bits in (32, 4):
    res = np.mean([run(bits, s) for s in (1, 2)], 0)
    print("%s MLP, 5 stages, accuracy on ALL classes after each stage: %s" % ("float32" if bits == 32 else "4-bit", " ".join("%.1f" % v for v in res)), flush=True)
print("L Cortex on the same protocol (integer model, 2,000 images per stage): digits 94.2 %, clothing 81.5 %; the chip stores no examples.")
