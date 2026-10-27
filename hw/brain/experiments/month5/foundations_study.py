"""27 Oct 2026, SIMULATED. FOUNDATIONS STUDY: why do standard networks multiply, and what do we lose when we replace it? Same input everywhere (L's 4,608-bit detector code, Fashion-MNIST, 60,000 train / 10,000 test). Dense baselines are GPU-style references trained in numpy (reference only, not our chip).
E1 precision ladder: a linear (softmax) model and a one-hidden-layer network trained in float, then weights quantised after training (int8, 4-bit, 2-bit, ternary, 1-bit sign); our integer counting table (L) and our table with clause bits as references.
E2 credit assignment: the same one-hidden-layer network trained with (a) backprop float, (b) backprop with ternary weights (straight-through), (c) backprop with ternary weights AND binary hidden activations (add-only inference), (d) feedback alignment (random fixed backward weights, no weight transport), (e) frozen random hidden layer with a trained readout (no credit assignment to the hidden layer).
E3 interpolation: inputs damaged by removing 10/20/30% of the active bits and adding the same number of random bits, and by blanking a 3x3 block of grid positions; models trained on clean data.
E4 add-only inference: operation counts and energy for each model (Horowitz 45 nm constants as elsewhere in the project: ESTIMATED).
env: EP epochs, H hidden units."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table
E_ = lambda k, d: type(d)(os.environ.get(k, d)); EP = E_("EP", 8); H = E_("H", 256); t0 = time.time()
Xtr, Xte = ctr.astype(np.float32), cte.astype(np.float32); D, K = Xtr.shape[1], 10; rs = np.random.RandomState(0); BS = 128
def ptq(W, bits):                                                                                  # post-training quantisation of one weight tensor
    if bits == "ternary": a = np.abs(W).mean(); return a * np.clip(np.round(W / (a + 1e-12)), -1, 1)
    if bits == 1: return np.abs(W).mean() * np.sign(W)
    m = np.abs(W).max() + 1e-12; L = 2 ** (bits - 1) - 1; return np.round(W / m * L) / L * m
def tern(W): a = np.abs(W).mean() + 1e-12; return a * np.clip(np.round(W / a), -1, 1)
def softmax(z): z = z - z.max(1, keepdims=True); e = np.exp(z); return e / e.sum(1, keepdims=True)
class Net:
    def __init__(s, hidden, mode, seed=0):
        r = np.random.RandomState(seed); s.hidden = hidden; s.mode = mode; s.h = hidden > 0
        if s.h: s.W1 = (r.randn(D, hidden) * np.sqrt(2.0 / 50)).astype(np.float32); s.b1 = np.zeros(hidden, np.float32); s.W2 = (r.randn(hidden, K) * np.sqrt(1.0 / hidden)).astype(np.float32); s.b2 = np.zeros(K, np.float32); s.B2 = (r.randn(K, hidden) * 0.3).astype(np.float32)
        else: s.W2 = np.zeros((D, K), np.float32); s.b2 = np.zeros(K, np.float32)
        s.opt = {}
    def q(s, W): return tern(W) if "ternary" in s.mode else W
    def fwd(s, X, quant=None):
        W1 = quant(s.W1) if quant and s.h else (s.q(s.W1) if s.h else None); W2 = quant(s.W2) if quant else s.q(s.W2)
        if not s.h: return None, X @ W2 + s.b2, None, W2
        z1 = X @ W1 + s.b1; hh = (z1 > 0).astype(np.float32) if "bin" in s.mode else np.maximum(z1, 0); return z1, hh @ W2 + s.b2, hh, (W1, W2)
    def adam(s, name, p, g, lr=1e-3):
        m, v, t = s.opt.get(name, (np.zeros_like(p), np.zeros_like(p), 0)); t += 1; m = 0.9 * m + 0.1 * g; v = 0.999 * v + 0.001 * g * g; s.opt[name] = (m, v, t); p -= lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
    def step(s, X, y):
        B = len(X); Y = np.eye(K, dtype=np.float32)[y]
        if not s.h:
            _, lo, _, W2 = s.fwd(X); dz = (softmax(lo) - Y) / B; s.adam("W2", s.W2, X.T @ dz); s.adam("b2", s.b2, dz.sum(0)); return
        z1, lo, hh, (W1, W2) = s.fwd(X); dz2 = (softmax(lo) - Y) / B
        if s.mode == "random": s.adam("W2", s.W2, hh.T @ dz2); s.adam("b2", s.b2, dz2.sum(0)); return
        dh = dz2 @ (s.B2 if s.mode == "fa" else W2.T)
        dz1 = dh * ((np.abs(z1) < 1.0) if "bin" in s.mode else (z1 > 0)); s.adam("W2", s.W2, hh.T @ dz2); s.adam("b2", s.b2, dz2.sum(0)); s.adam("W1", s.W1, X.T @ dz1); s.adam("b1", s.b1, dz1.sum(0))
    def acc(s, X, y, quant=None):
        out = []
        for i in range(0, len(X), 5000): out.append(s.fwd(X[i:i + 5000], quant)[1].argmax(1))
        p = np.concatenate(out); return (p == y).mean(), p
def train(net, ep):
    for e in range(ep):
        order = rs.permutation(len(Xtr))
        for i in range(0, len(order), BS): j = order[i:i + BS]; net.step(Xtr[j], ytr[j])
    return net
res = {}
def P(tag, acc, extra=""): res[tag] = acc; print("RESULT %-58s acc %.4f %s [%.0fs]" % (tag, acc, extra, time.time() - t0), flush=True)
# E1 + E2
W = train_table(ctr, ytr); P("counting table L (integer counters, margin rule)", ((cte.astype(np.int32) @ W).argmax(1) == yte).mean())
nets = {}
for name, hid, mode in (("linear float", 0, "float"), ("MLP float (backprop)", H, "float"), ("MLP ternary weights (backprop STE)", H, "ternary"), ("MLP ternary + binary hidden (add-only)", H, "ternary_bin"), ("MLP feedback alignment", H, "fa"), ("MLP frozen random hidden layer", H, "random")):
    nets[name] = train(Net(hid, mode), EP if hid else EP); a, _ = nets[name].acc(Xte, yte); P(name, a)
for name in ("linear float", "MLP float (backprop)"):
    for bits in (8, 4, 2, "ternary", 1):
        a, _ = nets[name].acc(Xte, yte, quant=lambda W, b=bits: ptq(W, b)); P("%s, weights quantised after training to %s" % (name, bits), a)
# E3 interpolation
def damage(X, frac, rs_):
    Z = X.copy()
    for i in range(len(Z)):
        on = np.where(Z[i] > 0)[0]; k = int(len(on) * frac); off_idx = rs_.choice(on, k, replace=False); Z[i, off_idx] = 0; Z[i, rs_.choice(D, k, replace=False)] = 1
    return Z
def blank(X):
    Z = X.reshape(len(X), 4, 6, 6, 32).copy(); Z[:, :, 1:4, 1:4, :] = 0; return Z.reshape(len(X), -1)
r3 = np.random.RandomState(5); tests = {"clean": Xte}
for f in (0.1, 0.2, 0.3): tests["remove+add %d%% of active bits" % (100 * f)] = damage(Xte[:5000], f, r3)
tests["blank a 3x3 block of positions"] = blank(Xte[:5000]); ys = {k: (yte if k == "clean" else yte[:5000]) for k in tests}
for tn, Xd in tests.items():
    Sw = Xd.astype(np.int32) @ W; P("E3 %-38s | counting table L" % tn, (Sw.argmax(1) == ys[tn]).mean())
    for name in ("linear float", "MLP float (backprop)", "MLP ternary weights (backprop STE)", "MLP ternary + binary hidden (add-only)"): P("E3 %-38s | %s" % (tn, name), nets[name].acc(Xd, ys[tn])[0])
# E4 operations and energy (ESTIMATED, 45 nm: fp32 mult 3.7 pJ, fp32 add 0.9 pJ, int32 add 0.1 pJ, int8 add 0.03 pJ, 64-bit SRAM read 20 pJ for a 32 KB array, 100 pJ for 1 MB)
act = Xte.sum(1).mean(); print("E4 average active input bits per image: %.0f of %d" % (act, D), flush=True)
def en(mult, add, words, sram): return (mult * 3.7 + add * 0.9 + words * sram) / 1000
rows = [("MLP float, dense", D * H + H * K, D * H + H * K, (D * H + H * K) * 32 / 64, 100.0), ("MLP float, event-driven (skip zero inputs)", act * H + H * K, act * H + H * K, (act * H + H * K) * 32 / 64, 100.0)]
for nm, mu, ad, wd, sr in rows: print("E4 %-52s mults %9.0f adds %9.0f weight words %9.0f -> %.1f nJ" % (nm, mu, ad, wd, en(mu, ad, wd, sr)), flush=True)
print("E4 %-52s mults %9.0f adds %9.0f weight words %9.0f -> %.1f nJ" % ("MLP ternary weights + binary hidden, event-driven", 0, act * H + (res.get('hid_on', 0.5) * H * K), act * H * 2 / 64 + H * K * 2 / 64, (act * H * 0.1 + 0.5 * H * K * 0.1 + (act * H * 2 / 64 + H * K * 2 / 64) * 100.0) / 1000), flush=True)
print("E4 %-52s mults %9.0f adds %9.0f weight words %9.0f -> %.1f nJ" % ("counting table L (10 classes, 8-bit entries)", 0, act * K, act * K * 8 / 64, (act * K * 0.1 + act * K * 8 / 64 * 100.0) / 1000), flush=True)
