"""25 Oct 2026, SIMULATED, Fashion-MNIST. Stage A: train the hard-gate integer learner (error passed down, as bool_hardint.py) ONCE on base classes 0-5 (T-shirt, Trouser, Pullover, Dress, Coat, Sandal) on L's 4,608-bit code, then freeze it. Saves the gate layers' output bits for all images.
Shirt (6), Sneaker (7), Bag (8), Boot (9) are NEW classes seen only by the counting table later (bool_frozen_tables.py): tests whether frozen deep gate features help learn Shirt in stages. env: N1 N2 EPOCHS BATCH CLAMP"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte
E = lambda k, d: type(d)(os.environ.get(k, d))
N1, N2, EPOCHS, BATCH, CLAMP, LV = E("N1", 2000), E("N2", 2000), E("EPOCHS", 4), E("BATCH", 1000), E("CLAMP", 1000), 15
BASE = [0, 1, 2, 3, 4, 5]; G = 100; rs = np.random.RandomState(0); TAU = 10.0
m = np.isin(ytr, BASE); Xtr, Ytr = ctr[m].astype(np.int8), ytr[m]
sizes = [Xtr.shape[1], N1, N2, G * len(BASE)]; wiring = [(rs.randint(0, sizes[i], sizes[i + 1]), rs.randint(0, sizes[i], sizes[i + 1])) for i in range(3)]
TT = np.array([[[(g >> (2 * a + b)) & 1 for b in (0, 1)] for a in (0, 1)] for g in range(16)], np.int32)
C = [np.zeros((sizes[i + 1], 16), np.int32) for i in range(3)]
for c in C: c[:, 12] = 5
cls = np.repeat(np.arange(len(BASE)), G); remap = {c: i for i, c in enumerate(BASE)}; Yb = np.array([remap[c] for c in Ytr])
def forward(X):
    acts = [X]
    for i in range(3):
        g = C[i].argmax(1); a = acts[-1][:, wiring[i][0]]; b = acts[-1][:, wiring[i][1]]; acts.append(TT[g[None, :], a, b].astype(np.int8))
    return acts
t0 = time.time()
for ep in range(EPOCHS):
    perm = rs.permutation(len(Xtr))
    for k in range(0, len(perm) - BATCH + 1, BATCH):
        idx = perm[k:k + BATCH]; acts = forward(Xtr[idx]); y = Yb[idx]; gates = [C[i].argmax(1) for i in range(3)]
        s = acts[3].reshape(BATCH, len(BASE), G).sum(2) / TAU; p = np.exp(s - s.max(1, keepdims=True)); p /= p.sum(1, keepdims=True); d = p - np.eye(len(BASE))[y]
        e = np.round(d / (np.abs(d).max() + 1e-12) * LV).astype(np.int32)[:, cls]
        for i in (2, 1, 0):
            ia, ib = wiring[i]; a = acts[i][:, ia]; b = acts[i][:, ib]
            S = np.einsum("nj,njg->jg", e, TT[np.arange(16)[None, None, :], a[:, :, None], b[:, :, None]]); S = S - S.sum(1, keepdims=True) // 16; C[i] = np.clip(C[i] - np.sign(S), -CLAMP, CLAMP).astype(np.int32)
            if i == 0: break
            g = gates[i]; dA = TT[g[None, :], 1, b] - TT[g[None, :], 0, b]; dB = TT[g[None, :], a, 1] - TT[g[None, :], a, 0]; n_prev = sizes[i]; flat = np.arange(BATCH)[:, None] * n_prev
            err = np.bincount((flat + ia[None, :]).ravel(), weights=(e * dA).ravel(), minlength=BATCH * n_prev) + np.bincount((flat + ib[None, :]).ravel(), weights=(e * dB).ravel(), minlength=BATCH * n_prev)
            e = np.clip(np.round(err), -LV, LV).reshape(BATCH, n_prev).astype(np.int32)
    mt = np.isin(yte, BASE); s = np.concatenate([forward(cte[mt][i:i + 5000].astype(np.int8))[3].reshape(-1, len(BASE), G).sum(2) for i in range(0, mt.sum(), 5000)])
    print("stage A epoch %d: accuracy on base classes (6-way) %.4f | %.0fs" % (ep + 1, (s.argmax(1) == np.array([remap[c] for c in yte[mt]])).mean(), time.time() - t0), flush=True)
def feats(X): return np.concatenate([np.concatenate(forward(X[i:i + 5000].astype(np.int8))[1:], 1) for i in range(0, len(X), 5000)]).astype(np.uint8)
np.savez_compressed("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/frozen_feats.npz", ftr=feats(ctr), fte=feats(cte), sizes=np.array(sizes[1:]))
print("saved frozen gate features", flush=True)
