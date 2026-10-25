"""25 Oct 2026, SIMULATED, Fashion-MNIST. Idea 3: label-free integer gate learner (no labels, no stored images, hard gates, integer error, counters moved by sign steps).
Input: 2 thresholds per pixel (1,568 bits). Gate layers [N1, N2, NOUT]. For every image two views (random shift of up to 2 pixels, 3% bit drop) are coded; the error on each output bit is
   e = A * (out_view1 - out_view2)  [same image, same code]  +  B * (2*out_view1 - 1) * [out_view1 == out_of_a_random_other_image]  [different image, push away where the codes agree]
passed down the layers with truth-table derivatives, as in bool_hardint.py. After training, the codes are frozen and read by L's counting table (labels used only there).
env: N1 N2 NOUT EPOCHS BATCH A B CLAMP SEED"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, xte, ctr, cte, ytr, yte, train_table, report
E = lambda k, d: type(d)(os.environ.get(k, d))
N1, N2, NOUT, EPOCHS, BATCH, A, B, CLAMP, SEED, LV = E("N1", 1000), E("N2", 1000), E("NOUT", 1000), E("EPOCHS", 6), E("BATCH", 500), E("A", 2), E("B", 1), E("CLAMP", 1000), E("SEED", 0), 15
rs = np.random.RandomState(SEED)
def bits(x): return np.concatenate([x > 85, x > 170], 1).astype(np.int8)
def view(x):
    im = x.reshape(-1, 28, 28); out = np.zeros_like(im); dy, dx = rs.randint(-2, 3, 2)
    ys, yd = (slice(0, 28 - dy), slice(dy, 28)) if dy >= 0 else (slice(-dy, 28), slice(0, 28 + dy)); xs, xd = (slice(0, 28 - dx), slice(dx, 28)) if dx >= 0 else (slice(-dx, 28), slice(0, 28 + dx))
    out[:, yd, xd] = im[:, ys, xs]; b = bits(out.reshape(len(x), -1)); b[rs.rand(*b.shape) < 0.03] = 0; return b
sizes = [1568, N1, N2, NOUT]; W = [(rs.randint(0, sizes[i], sizes[i + 1]), rs.randint(0, sizes[i], sizes[i + 1])) for i in range(3)]
TT = np.array([[[(g >> (2 * a + b)) & 1 for b in (0, 1)] for a in (0, 1)] for g in range(16)], np.int32); AR = np.arange(16)[None, None, :]
C = []
for n in sizes[1:]: c = np.zeros((n, 16), np.int32); c[:, 12] = 5; C.append(c)
def fwd(X):
    acts = [X]
    for i in range(3):
        g = C[i].argmax(1); acts.append(TT[g[None, :], acts[-1][:, W[i][0]], acts[-1][:, W[i][1]]].astype(np.int8))
    return acts
def upd(Cm, e, a, b):
    S = np.einsum("nj,njg->jg", e, TT[AR, a[:, :, None], b[:, :, None]]); S = S - S.sum(1, keepdims=True) // 16; return np.clip(Cm - np.sign(S), -CLAMP, CLAMP).astype(np.int32)
def down(e, Cm, ia, ib, a, b, n_prev):
    g = Cm.argmax(1); dA = TT[g[None, :], 1, b] - TT[g[None, :], 0, b]; dB = TT[g[None, :], a, 1] - TT[g[None, :], a, 0]; flat = np.arange(len(e))[:, None] * n_prev
    r = np.bincount((flat + ia[None, :]).ravel(), weights=(e * dA).ravel(), minlength=len(e) * n_prev) + np.bincount((flat + ib[None, :]).ravel(), weights=(e * dB).ravel(), minlength=len(e) * n_prev)
    return np.clip(np.round(r), -LV, LV).reshape(len(e), n_prev).astype(np.int32)
t0 = time.time()
for ep in range(EPOCHS):
    perm = rs.permutation(len(xtr)); inv = 0.0; far = 0.0; bal = 0.0
    for k in range(0, len(perm) - BATCH + 1, BATCH):
        idx = perm[k:k + BATCH]; v1 = view(xtr[idx]); v2 = view(xtr[idx]); X = np.concatenate([v1, v2]); acts = fwd(X)
        o1, o2 = acts[3][:BATCH].astype(np.int32), acts[3][BATCH:].astype(np.int32); oneg = np.roll(o1, 1, axis=0)
        e1 = A * (o1 - o2) + B * (2 * o1 - 1) * (o1 == oneg); e2 = A * (o2 - o1) + B * (2 * o2 - 1) * (o2 == np.roll(o2, 1, axis=0))
        e = np.clip(np.concatenate([e1, e2]) * (LV // max(1, A + B)), -LV, LV).astype(np.int32)
        inv += np.abs(o1 - o2).mean(); far += (o1 != oneg).mean(); bal += o1.mean()
        for i in (2, 1, 0):
            ia, ib = W[i]; a = acts[i][:, ia]; b = acts[i][:, ib]; C[i] = upd(C[i], e, a, b)
            if i > 0: e = down(e, C[i], ia, ib, a, b, sizes[i])
    nb = len(perm) // BATCH; print("[%4.0fs] epoch %d: bit disagreement between views %.3f | bit disagreement between different images %.3f | mean bit activity %.3f" % (time.time() - t0, ep + 1, inv / nb, far / nb, bal / nb), flush=True)
def feats(X, upto=3):
    return np.concatenate([np.concatenate(fwd(bits(X[i:i + 5000]))[1:], 1) for i in range(0, len(X), 5000)]).astype(np.uint8)
ftr, fte = feats(xtr), feats(xte)
def run(tag, Ftr, Fte):
    W0 = train_table(Ftr, ytr); sc = Fte.astype(np.int32) @ W0; print("[%4.0fs] bits %6d active %5.0f | " % (time.time() - t0, Ftr.shape[1], Ftr.sum(1).mean()), end=""); report(tag, sc)
run("label-free gate features alone (all layers)", ftr, fte)
run("L code + label-free gate features", np.concatenate([ctr, ftr], 1), np.concatenate([cte, fte], 1))
