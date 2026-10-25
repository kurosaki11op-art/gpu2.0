"""25 Oct 2026, SIMULATED, MNIST, hard-gate integer learner, joint training of 10 classes. Is the local-learning gap head capacity?
MODE=0: error from the output layer passed down through all layers (end-to-end).
MODE=1: each hidden layer has its own readout (popcount of its nodes tagged by class); its own error updates only that layer (k=1 head).
MODE=2: each hidden layer gets an auxiliary head of HEADN gates (one extra gate layer, groups by class); the head's error is passed through the head into its layer only, never further (k=2 head, as in greedy layer-wise learning).
env: MODE EPOCHS N1 N2 HEADN BATCH CLAMP SEED"""
import os, time
import numpy as np
E = lambda k, d: type(d)(os.environ.get(k, d))
MODE, EPOCHS, N1, N2, HEADN, BATCH, CLAMP, LV, SEED = E("MODE", 0), E("EPOCHS", 4), E("N1", 500), E("N2", 500), E("HEADN", 500), E("BATCH", 1000), E("CLAMP", 1000), 15, E("SEED", 0)
rs = np.random.RandomState(SEED); G = 100
DATA = os.environ.get("DATA", "mnist")
if DATA == "fashion":                                                                                       # L's own 4,608-bit code on Fashion-MNIST (cached by shirt_new_methods_setup.py)
    import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
    from shirt_new_methods_setup import ctr, cte, ytr, yte
    Xtr, Xte = ctr.astype(np.int8), cte.astype(np.int8)
else:
    z = np.load("/tmp/mnistdata/mnist.npz"); xtr = z["x_train"].reshape(-1, 784); ytr = z["y_train"].astype(np.int64); xte = z["x_test"].reshape(-1, 784); yte = z["y_test"].astype(np.int64)
    bits = lambda x: np.concatenate([x > 85, x > 170], 1).astype(np.int8); Xtr, Xte = bits(xtr), bits(xte)
sizes = [Xtr.shape[1], N1, N2, 10 * G]; W = [(rs.randint(0, sizes[i], sizes[i + 1]), rs.randint(0, sizes[i], sizes[i + 1])) for i in range(3)]
TT = np.array([[[(g >> (2 * a + b)) & 1 for b in (0, 1)] for a in (0, 1)] for g in range(16)], np.int32); AR = np.arange(16)[None, None, :]
def init(n): c = np.zeros((n, 16), np.int32); c[:, 12] = 5; return c
C = [init(sizes[i + 1]) for i in range(3)]
tag = [rs.permutation(np.arange(sizes[i + 1]) % 10) for i in range(2)] + [np.repeat(np.arange(10), G)]
HW = [(rs.randint(0, sizes[i + 1], HEADN), rs.randint(0, sizes[i + 1], HEADN)) for i in range(2)]; HC = [init(HEADN) for _ in range(2)]; htag = np.repeat(np.arange(10), HEADN // 10)
def fwd(X):
    acts = [X]
    for i in range(3):
        g = C[i].argmax(1); acts.append(TT[g[None, :], acts[-1][:, W[i][0]], acts[-1][:, W[i][1]]].astype(np.int8))
    return acts
ERRMODE, MARG, SH = os.environ.get("ERRMODE", "softmax"), E("MARG", 20), E("SH", 1)
def err(out, tg, y):
    if ERRMODE == "margin":                                       # integer only: group sums, subtract, compare, shift, clip (no exponential, no division, no multiply)
        s = np.stack([out[:, tg == c].sum(1) for c in range(10)], 1).astype(np.int32); st = s[np.arange(len(y)), y][:, None]
        need = s - st + MARG; need[np.arange(len(y)), y] = 0; need = np.where(need > 0, need, 0); ek = np.minimum(need >> SH, LV)         # every class scoring within MARG of the true class is pushed down by how much it violates
        et = -np.minimum(ek.sum(1), 127); ek[np.arange(len(y)), y] = et                                                                  # the true class is pushed up by the SUM of the violations, so the errors balance as softmax's do
        return ek.astype(np.int32)[:, tg]
    s = np.stack([out[:, tg == c].sum(1) for c in range(10)], 1) / max(1.0, len(tg) / 10 / 10); p = np.exp(s - s.max(1, keepdims=True)); p /= p.sum(1, keepdims=True); d = p - np.eye(10)[y]
    return np.round(d / (np.abs(d).max() + 1e-12) * LV).astype(np.int32)[:, tg]
def upd(Cm, e, a, b):
    S = np.einsum("nj,njg->jg", e, TT[AR, a[:, :, None], b[:, :, None]]); S = S - S.sum(1, keepdims=True) // 16; return np.clip(Cm - np.sign(S), -CLAMP, CLAMP).astype(np.int32)
def down(e, Cm, ia, ib, a, b, n_prev):
    g = Cm.argmax(1); dA = TT[g[None, :], 1, b] - TT[g[None, :], 0, b]; dB = TT[g[None, :], a, 1] - TT[g[None, :], a, 0]; flat = np.arange(len(e))[:, None] * n_prev
    r = np.bincount((flat + ia[None, :]).ravel(), weights=(e * dA).ravel(), minlength=len(e) * n_prev) + np.bincount((flat + ib[None, :]).ravel(), weights=(e * dB).ravel(), minlength=len(e) * n_prev)
    return np.clip(np.round(r), -LV, LV).reshape(len(e), n_prev).astype(np.int32)
def evaluate(): return (np.concatenate([fwd(Xte[i:i + 5000].astype(np.int8))[3].reshape(-1, 10, G).sum(2) for i in range(0, len(Xte), 5000)]).argmax(1) == yte).mean()
t0 = time.time()
for ep in range(EPOCHS):
    perm = rs.permutation(len(Xtr))
    for k in range(0, len(perm) - BATCH + 1, BATCH):
        idx = perm[k:k + BATCH]; acts = fwd(Xtr[idx]); y = ytr[idx]
        e = err(acts[3], tag[2], y)
        for i in (2, 1, 0):
            ia, ib = W[i]; a = acts[i][:, ia]; b = acts[i][:, ib]
            if i < 2 and MODE == 1: e = err(acts[i + 1], tag[i], y)
            if i < 2 and MODE == 2:
                ha, hb = HW[i]; ha_a = acts[i + 1][:, ha]; ha_b = acts[i + 1][:, hb]; hg = HC[i].argmax(1); hout = TT[hg[None, :], ha_a, ha_b].astype(np.int8)
                eh = err(hout, htag, y); Hold = HC[i]; HC[i] = upd(HC[i], eh, ha_a, ha_b); e = down(eh, Hold, ha, hb, ha_a, ha_b, sizes[i + 1])               # through the head into this layer only
            Cold = C[i]; C[i] = upd(C[i], e, a, b)
            if MODE == 0 and i > 0: e = down(e, Cold, ia, ib, a, b, sizes[i])
    print("MODE=%d epoch %d: test acc %.4f | %.0fs" % (MODE, ep + 1, evaluate(), time.time() - t0), flush=True)

if DATA == "fashion":
    sc = np.concatenate([fwd(Xte[i:i + 5000].astype(np.int8))[3].reshape(-1, 10, G).sum(2) for i in range(0, len(Xte), 5000)]).astype(np.float32); CLs = np.array([0, 2, 4, 6]); mk = np.isin(yte, CLs)
    s6 = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("FASHION: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f" % ((sc.argmax(1) == yte).mean(), (CLs[sc[mk][:, CLs].argmax(1)] == yte[mk]).mean(), (sc.argmax(1)[yte == 6] == 6).mean(), ap))
