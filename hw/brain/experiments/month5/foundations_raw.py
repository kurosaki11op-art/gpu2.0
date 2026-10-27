"""27 Oct 2026, SIMULATED. FOUNDATIONS E5: where do multiplication, depth and weight sharing matter? Raw 28x28 pixels (scaled 0-1), Fashion-MNIST, numpy reference models (not our chip): softmax regression, one-hidden-layer MLP, and a small convolutional network (3x3 conv with 16 filters shared over all positions, ReLU, 2x2 max pool, linear readout), each in float, and the CNN/MLP with ternary weights (straight-through training: inference needs adds and subtracts only, one scale per layer). Same Adam optimiser and epochs everywhere. env: EP."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, xte, ytr, yte
E_ = lambda k, d: type(d)(os.environ.get(k, d)); EP = E_("EP", 6); t0 = time.time(); rs = np.random.RandomState(0); BS = 128; K = 10
Xtr = (xtr.reshape(-1, 28, 28) / 255.0).astype(np.float32); Xte = (xte.reshape(-1, 28, 28) / 255.0).astype(np.float32)
def tern(W): a = np.abs(W).mean() + 1e-12; return a * np.clip(np.round(W / a), -1, 1)
def softmax(z): z = z - z.max(1, keepdims=True); e = np.exp(z); return e / e.sum(1, keepdims=True)
class Adam:
    def __init__(s): s.st = {}
    def __call__(s, k, p, g, lr=1e-3):
        m, v, t = s.st.get(k, (np.zeros_like(p), np.zeros_like(p), 0)); t += 1; m = 0.9 * m + 0.1 * g; v = 0.999 * v + 0.001 * g * g; s.st[k] = (m, v, t); p -= lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
def patches(X):                                                                                     # (B,28,28) -> (B,26,26,9)
    return np.stack([X[:, i:i + 26, j:j + 26] for i in range(3) for j in range(3)], -1)
class Model:
    def __init__(s, kind, ternary, F=16, H=256, cb=0, tc=None):
        r = np.random.RandomState(1); s.kind = kind; s.t = ternary; s.cb = cb; s.tc = ternary if tc is None else tc; s.opt = Adam(); s.F = F
        if kind == "linear": s.W = np.zeros((784, K), np.float32); s.b = np.zeros(K, np.float32)
        if kind == "mlp": s.W1 = (r.randn(784, H) * np.sqrt(2 / 784)).astype(np.float32); s.b1 = np.zeros(H, np.float32); s.W = (r.randn(H, K) * np.sqrt(1 / H)).astype(np.float32); s.b = np.zeros(K, np.float32)
        if kind == "cnn": s.Wc = (r.randn(9, F) * np.sqrt(2 / 9)).astype(np.float32); s.bc = np.zeros(F, np.float32); s.W = (r.randn(13 * 13 * F, K) * np.sqrt(1 / (169 * F))).astype(np.float32); s.b = np.zeros(K, np.float32)
    def q(s, W): return tern(W) if s.t else W
    def qc(s, W):
        if not s.cb: return tern(W) if s.tc else W
        m = np.abs(W).max() + 1e-12; L = 2 ** (s.cb - 1) - 1; return np.round(W / m * L) / L * m
    def forward(s, X):
        B = len(X); c = {}
        if s.kind == "linear": c["x"] = X.reshape(B, -1); return c["x"] @ s.q(s.W) + s.b, c
        if s.kind == "mlp": c["x"] = X.reshape(B, -1); c["z"] = c["x"] @ s.q(s.W1) + s.b1; c["h"] = np.maximum(c["z"], 0); return c["h"] @ s.q(s.W) + s.b, c
        P = patches(X); c["P"] = P; z = P @ s.qc(s.Wc) + s.bc; c["z"] = z; a = np.maximum(z, 0); a4 = a.reshape(B, 13, 2, 13, 2, s.F); pool = a4.max((2, 4)); c["mask"] = (a4 == pool[:, :, None, :, None, :]); c["pool"] = pool; return pool.reshape(B, -1) @ s.q(s.W) + s.b, c
    def step(s, X, y):
        lo, c = s.forward(X); B = len(X); dz = (softmax(lo) - np.eye(K, dtype=np.float32)[y]) / B
        if s.kind == "linear": s.opt("W", s.W, c["x"].T @ dz); s.opt("b", s.b, dz.sum(0)); return
        if s.kind == "mlp":
            dh = dz @ s.q(s.W).T * (c["z"] > 0); s.opt("W", s.W, c["h"].T @ dz); s.opt("b", s.b, dz.sum(0)); s.opt("W1", s.W1, c["x"].T @ dh); s.opt("b1", s.b1, dh.sum(0)); return
        dp = (dz @ s.q(s.W).T).reshape(B, 13, 13, s.F); da = (c["mask"] * dp[:, :, None, :, None, :]).reshape(B, 26, 26, s.F) * (c["z"] > 0)
        s.opt("W", s.W, c["pool"].reshape(B, -1).T @ dz); s.opt("b", s.b, dz.sum(0)); s.opt("Wc", s.Wc, c["P"].reshape(-1, 9).T @ da.reshape(-1, s.F)); s.opt("bc", s.bc, da.sum((0, 1, 2)))
    def acc(s, X, y): p = np.concatenate([s.forward(X[i:i + 1000])[0].argmax(1) for i in range(0, len(X), 1000)]); return (p == y).mean()
FIL = E_("F", 16); ONLY = E_("ONLY", "")
HYB = E_("HYB", 0)
for kind, ternary, nm in (("linear", False, "softmax regression, float"), ("mlp", False, "MLP 256 hidden, float"), ("mlp", True, "MLP 256 hidden, ternary weights"), ("cnn", False, "CNN %d shared 3x3 filters, float" % FIL), ("cnn", True, "CNN %d shared 3x3 filters, ternary weights" % FIL)):
    if ONLY and kind != ONLY: continue
    m = Model(kind, ternary, F=FIL, cb=HYB if kind == 'cnn' and ternary else 0)
    if HYB and kind == 'cnn' and ternary: nm = nm + " (conv filters %d-bit, readout ternary)" % HYB
    for e in range(EP):
        order = rs.permutation(len(Xtr))
        for i in range(0, len(order), BS): j = order[i:i + BS]; m.step(Xtr[j], ytr[j])
        if e in (0, EP - 1): print("  %-45s epoch %d: test acc %.4f [%.0fs]" % (nm, e + 1, m.acc(Xte, yte), time.time() - t0), flush=True)
    print("RESULT raw pixels, %-45s acc %.4f" % (nm, m.acc(Xte, yte)), flush=True)

MIX = E_("MIX", "")
if MIX:                                                                                             # which layer carries the loss when weights become ternary?
    for tc, tr, nm in ((True, False, "conv filters ternary, readout float"), (False, True, "conv filters float, readout ternary")):
        m = Model("cnn", tr, F=FIL, tc=tc); r_ = np.random.RandomState(0)
        for e in range(EP):
            order = r_.permutation(len(Xtr))
            for i in range(0, len(order), BS): j = order[i:i + BS]; m.step(Xtr[j], ytr[j])
        print("RESULT raw pixels, CNN %d filters, %-40s acc %.4f" % (FIL, nm, m.acc(Xte, yte)), flush=True)
