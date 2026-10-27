"""27 Oct 2026, SIMULATED. FRONT-END TEST: does sending the task's error back to the pattern finders ('the eyes') raise what L's counting table can reach? Small stand-in for L's front end: input = two binary channels (pixel > 50, pixel > 150), 5x5 patches, 128 shared pattern finders (ReLU responses), 4x4 max pooling -> 6 x 6 x 128 = 4,608 features (the size of L's code). The eyes are trained jointly with an auxiliary float linear readout V on the real pooled responses; the error e = softmax - label reaches the eyes through
  bp     : V transposed (exact backprop, the ceiling for this front end),
  fa     : a random FIXED dense matrix B (feedback alignment, no weight transport),
  sparse : a random fixed SPARSE +-1 matrix (about 10% non-zero; the error is added or subtracted, no multiply),
  none   : the eyes are never trained (random filters).
After training, the pooled responses are binarised (on above a per-feature quantile, about 13% active like L's code) and read by OUR counting table (integers, margin rule). Reported: the network's own float readout, a float readout on the binary code, and our counting table on the binary code. Reference: L's Hebbian code + the same table 88.85.
env: MODE (bp|fa|sparse|none), EP epochs, F filters, Q quantile."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, xte, ytr, yte, train_table
E_ = lambda k, d: type(d)(os.environ.get(k, d)); MODE = E_("MODE", "bp"); EP = E_("EP", 4); F = E_("F", 128); Q = E_("Q", 0.87); t0 = time.time(); BS = 128; K = 10; SEED = E_("SEED", 0); POOL = E_("POOL", 4); REAL = E_("REAL", 0); THR = [int(v) for v in E_("THR", "50,150").split(",")]; NC = 1 if REAL else len(THR); G = 24 // POOL
def chans(x):
    im = x.reshape(-1, 28, 28)
    return (im[..., None] / 255.0).astype(np.float32) if REAL else np.stack([(im > t) for t in THR], -1).astype(np.float32)
Xtr, Xte = chans(xtr), chans(xte)
def patches(X):                                                                                     # (B,28,28,2) -> (B,24,24,50)
    return np.concatenate([X[:, i:i + 24, j:j + 24, :] for i in range(5) for j in range(5)], -1)
r = np.random.RandomState(SEED); Wc = (r.randn(25 * NC, F) * np.sqrt(2 / (25 * NC))).astype(np.float32); bc = np.zeros(F, np.float32); V = np.zeros((G * G * F, K), np.float32); bV = np.zeros(K, np.float32)
NFEAT = G * G * F
Bfa = (r.randn(K, NFEAT) * 0.05).astype(np.float32); Bsp = (r.choice([-1.0, 0.0, 1.0], size=(K, NFEAT), p=[0.05, 0.9, 0.05]) * 0.05).astype(np.float32)
def softmax(z): z = z - z.max(1, keepdims=True); e = np.exp(z); return e / e.sum(1, keepdims=True)
class Adam:
    def __init__(s): s.st = {}
    def __call__(s, k, p, g, lr=1e-3):
        m, v, t = s.st.get(k, (np.zeros_like(p), np.zeros_like(p), 0)); t += 1; m = 0.9 * m + 0.1 * g; v = 0.999 * v + 0.001 * g * g; s.st[k] = (m, v, t); p -= lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
opt = Adam()
def forward(X):
    P = patches(X); z = P @ Wc + bc; a = np.maximum(z, 0); a6 = a.reshape(len(X), G, POOL, G, POOL, F); pool = a6.max((2, 4)); return P, z, a6, pool
def step(X, y):
    global Wc, bc, V, bV
    P, z, a6, pool = forward(X); B = len(X); flat = pool.reshape(B, -1); e = (softmax(flat @ V + bV) - np.eye(K, dtype=np.float32)[y]) / B
    opt("V", V, flat.T @ e); opt("bV", bV, e.sum(0))
    if MODE == "none": return
    fb = {"bp": lambda: e @ V.T, "fa": lambda: e @ Bfa, "sparse": lambda: e @ Bsp}[MODE]()                  # error delivered to each feature
    mask = (a6 == pool[:, :, None, :, None, :]); da = (mask * fb.reshape(B, G, G, F)[:, :, None, :, None, :]).reshape(B, 24, 24, F) * (z > 0)
    opt("Wc", Wc, P.reshape(-1, 25 * NC).T @ da.reshape(-1, F) * (1.0 if MODE == "bp" else 10.0)); opt("bc", bc, da.sum((0, 1, 2)))
def features(X): return np.concatenate([forward(X[i:i + 500])[3].reshape(min(500, len(X) - i), -1) for i in range(0, len(X), 500)])
rs = np.random.RandomState(1)
for ep in range(EP):
    order = rs.permutation(len(Xtr))
    for i in range(0, len(order), BS): j = order[i:i + BS]; step(Xtr[j], ytr[j])
    print("  %s epoch %d done [%.0fs]" % (MODE, ep + 1, time.time() - t0), flush=True)
Ftr, Fte = features(Xtr), features(Xte); own = ((Fte @ V + bV).argmax(1) == yte).mean()
thr = np.quantile(Ftr[::5], Q, axis=0); Btr, Bte = (Ftr > thr).astype(np.uint8), (Fte > thr).astype(np.uint8)
W = train_table(Btr, ytr); tab = ((Bte.astype(np.int32) @ W).argmax(1) == yte).mean()
Wf = np.zeros((NFEAT, K), np.float32); bf = np.zeros(K, np.float32); o2 = Adam(); r2 = np.random.RandomState(2); Af, Bf_ = Btr.astype(np.float32), Bte.astype(np.float32)
for ep in range(6):
    o = r2.permutation(len(Af))
    for i in range(0, len(o), 128): j = o[i:i + 128]; dz = (softmax(Af[j] @ Wf + bf) - np.eye(K, dtype=np.float32)[ytr[j]]) / len(j); o2("W", Wf, Af[j].T @ dz); o2("b", bf, dz.sum(0))
fl = ((Bf_ @ Wf + bf).argmax(1) == yte).mean()
Q2 = min(0.97, Q + 0.08); thr2 = np.quantile(Ftr[::5], Q2, axis=0); B2tr, B2te = np.concatenate([Btr, (Ftr > thr2)], 1).astype(np.uint8), np.concatenate([Bte, (Fte > thr2)], 1).astype(np.uint8)
W2 = train_table(B2tr, ytr); tab2 = ((B2te.astype(np.int32) @ W2).argmax(1) == yte).mean(); print("   2-level output code (%.0f active of %d bits): our counting table %.4f" % (B2te.sum(1).mean(), B2te.shape[1], tab2), flush=True)
print("RESULT %-7s eyes trained %d epochs: own float readout on real responses %.4f | float readout on the binary code %.4f | OUR counting table on the binary code (%.0f active of %d) %.4f  [L's Hebbian code + table: 0.8885] [%.0fs]" % (MODE, EP, own, fl, Bte.sum(1).mean(), NFEAT, tab, time.time() - t0), flush=True)
