"""24 Oct 2026, SIMULATED, MNIST, gate network learning with HARD gates in the learning pass (chip-legal forward): outputs are bits, every step is a lookup, integer add, compare or shift. (The output-layer softmax is the only non-integer step and is stood in for by a lookup table in a chip.)
Per batch: forward hard bits (gate = largest of its 16 counters, optional integer noise NZ for exploration); output error per bit = round(LV * (p_class - onehot) / batch maximum), a graded integer; backward through each layer: counters of gate g at node j get S[j,g] = sum over examples of error * output of truth table g, minus the mean over g, and move one STEP against the sign of S; the error passed to the layer below is the sum over the nodes it feeds of error * Boolean derivative (truth-table lookup), clipped to [-LV, LV].
env: EPOCHS N1 N2 BATCH LV STEP CLAMP NZ TAU SEED"""
import os, time
import numpy as np
E = lambda k, d: type(d)(os.environ.get(k, d))
EPOCHS, N1, N2, BATCH, LV, STEP, CLAMP, NZ, TAU, SEED = E("EPOCHS", 4), E("N1", 500), E("N2", 500), E("BATCH", 64), E("LV", 15), E("STEP", 1), E("CLAMP", 60), E("NZ", 0), E("TAU", 10.0), E("SEED", 0)
G = 100; rs = np.random.RandomState(SEED)
if os.environ.get("DATA", "mnist") == "fashion":                                                          # L's own 4,608-bit code (stride 1, pool 4) on Fashion-MNIST, cached by shirt_new_methods_setup.py
    import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
    from shirt_new_methods_setup import ctr, cte, ytr, yte
    Xtr, Xte = ctr.astype(np.int8), cte.astype(np.int8)
else:
    z = np.load("/tmp/mnistdata/mnist.npz"); xtr = z["x_train"].reshape(-1, 784); ytr = z["y_train"].astype(np.int64); xte = z["x_test"].reshape(-1, 784); yte = z["y_test"].astype(np.int64)
    bits = lambda x: np.concatenate([x > 85, x > 170], 1).astype(np.int8); Xtr, Xte = bits(xtr), bits(xte)
sizes = [Xtr.shape[1], N1, N2, 10 * G]; wiring = [(rs.randint(0, sizes[i], sizes[i + 1]), rs.randint(0, sizes[i], sizes[i + 1])) for i in range(3)]
TT = np.array([[[(g >> (2 * a + b)) & 1 for b in (0, 1)] for a in (0, 1)] for g in range(16)], np.int32)      # TT[g][a][b]; gate 12 passes input a
C = [np.zeros((sizes[i + 1], 16), np.int32) for i in range(3)]
for c in C: c[:, 12] = 5
def pick(i, noise):
    c = C[i] + (rs.randint(-NZ, NZ + 1, C[i].shape) if (noise and NZ) else 0); return c.argmax(1)
def forward(X, noise=False):
    acts = [X]; gates = []
    for i in range(3):
        g = pick(i, noise); gates.append(g); a = acts[-1][:, wiring[i][0]]; b = acts[-1][:, wiring[i][1]]; acts.append(TT[g[None, :], a, b].astype(np.int8))
    return acts, gates
def evaluate():
    s = np.concatenate([forward(Xte[i:i + 5000])[0][3].reshape(-1, 10, G).sum(2) for i in range(0, len(Xte), 5000)]); acc = (s.argmax(1) == yte).mean()
    if os.environ.get("DATA", "mnist") == "fashion":
        CL = np.array([0, 2, 4, 6]); mk = np.isin(yte, CL); sc = s[:, 6] - np.delete(s, 6, 1).max(1); yy = yte == 6; o = np.argsort(-sc); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
        print("   cluster %.4f | Shirt recall %.3f | Shirt AP %.3f" % ((CL[s[mk][:, CL].argmax(1)] == yte[mk]).mean(), (s.argmax(1)[yte == 6] == 6).mean(), ap))
    return acc
t0 = time.time(); cls = np.repeat(np.arange(10), G)
for ep in range(EPOCHS):
    perm = rs.permutation(len(Xtr))
    for k in range(0, len(perm) - BATCH + 1, BATCH):
        idx = perm[k:k + BATCH]; acts, gates = forward(Xtr[idx], True); y = ytr[idx]
        s = acts[3].reshape(BATCH, 10, G).sum(2) / TAU; p = np.exp(s - s.max(1, keepdims=True)); p /= p.sum(1, keepdims=True)    # lookup table on a chip
        d = p - np.eye(10)[y]; e = np.round(d / (np.abs(d).max() + 1e-12) * LV).astype(np.int32)[:, cls]                       # graded integer error per output bit
        for i in (2, 1, 0):
            ia, ib = wiring[i]; a = acts[i][:, ia]; b = acts[i][:, ib]
            S = np.einsum("nj,njg->jg", e, TT[np.arange(16)[None, None, :], a[:, :, None], b[:, :, None]]); S = S - S.sum(1, keepdims=True) // 16
            C[i] = np.clip(C[i] - STEP * np.sign(S), -CLAMP, CLAMP).astype(np.int32)
            if i == 0: break
            g = gates[i]; dA = TT[g[None, :], 1, b] - TT[g[None, :], 0, b]; dB = TT[g[None, :], a, 1] - TT[g[None, :], a, 0]; n_prev = sizes[i]; flat = np.arange(BATCH)[:, None] * n_prev
            err = np.bincount((flat + ia[None, :]).ravel(), weights=(e * dA).ravel(), minlength=BATCH * n_prev) + np.bincount((flat + ib[None, :]).ravel(), weights=(e * dB).ravel(), minlength=BATCH * n_prev)
            e = np.clip(np.round(err), -LV, LV).reshape(BATCH, n_prev).astype(np.int32)
    print("hard-forward integer learner epoch %d: test acc %.4f | %.0fs" % (ep + 1, evaluate(), time.time() - t0), flush=True)
