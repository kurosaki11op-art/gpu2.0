"""25 Oct 2026, SIMULATED, Fashion-MNIST. L-Deep v1: weight-shared gate trees trained by the integer error learner (no multiplies in the learning rule, no matrix products, hard gates, integer margin error, counters moved by sign steps).
Layer 1: F filters; each filter is a tree of 7 two-input gates (4 leaf gates read 8 fixed random bits of a 5x5 window over the two threshold planes, 2 middle gates, 1 root gate); the same gates are applied at every one of the 24x24 positions (weight sharing = counters summed over positions); OR pooling over 4x4 blocks gives F x 36 bits.
Then a flat gate layer of N2 gates (random wiring over the pooled bits) and an output layer of 1,000 gates read as 10 groups of 100 (popcount). Error: integer margin (as in bool_local_heads.py), passed down through truth-table derivatives; pooling passes the error to positions that agree with the direction.
env: F, N2, EPOCHS, BATCH, NIMG (images per epoch), MARG, SH, CLAMP, SEED"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, xte, ytr, yte
E = lambda k, d: type(d)(os.environ.get(k, d))
FREEZE = E("FREEZE", 0)
F, N2, EPOCHS, BATCH, NIMG, MARG, SH, CLAMP, SEED, LV = E("F", 16), E("N2", 1000), E("EPOCHS", 4), E("BATCH", 200), E("NIMG", 20000), E("MARG", 20), E("SH", 2), E("CLAMP", 1000), E("SEED", 0), 15
rs = np.random.RandomState(SEED); G = 100; NP = 24 * 24; PB = 6 * 6 * F
TT = np.array([[[(g >> (2 * a + b)) & 1 for b in (0, 1)] for a in (0, 1)] for g in range(16)], np.int32); AR = np.arange(16)[None, None, :]
def bits(x): im = x.reshape(-1, 28, 28); return np.stack([im > 85, im > 170], 1).astype(np.int8)                    # (N, 2, 28, 28)
def windows(P):                                                                                                         # (N, 576, 50) bits of every 5x5 window of both planes
    n = len(P); out = np.zeros((n, 24, 24, 2, 5, 5), np.int8)
    for dy in range(5):
        for dx in range(5): out[:, :, :, :, dy, dx] = P[:, :, dy:dy + 24, dx:dx + 24].transpose(0, 2, 3, 1)
    return out.reshape(n, NP, 50)
LA = np.stack([rs.choice(50, 8, replace=False) for _ in range(F)]).reshape(F, 4, 2)                                    # leaf inputs: 8 random window bits per filter, two per leaf
def init(n, *shape): c = rs.randint(0, 4, (n,) + shape + (16,)).astype(np.int32); c[..., 12] += 2; return c
C1 = init(F, 7)                                                                                                         # counters of the 7 tree gates of every filter, shared over positions: nodes 0-3 leaves, 4-5 middle, 6 root
sizes = [PB, N2, 10 * G]; W2 = [(rs.randint(0, sizes[i], sizes[i + 1]), rs.randint(0, sizes[i], sizes[i + 1])) for i in range(2)]
C2 = [np.zeros((sizes[i + 1], 16), np.int32) for i in range(2)]
for c in C2: c[:, 12] = 5
tag = np.repeat(np.arange(10), G)
def conv_forward(win):
    g = C1.argmax(2)                                                                                                   # (F, 7)
    wa = win[:, :, LA[:, :, 0]]; wb = win[:, :, LA[:, :, 1]]                                                           # (B, P, F, 4)
    leaf = TT[g[None, None, :, :4], wa, wb].astype(np.int8)
    m = np.stack([TT[g[None, None, :, 4], leaf[..., 0], leaf[..., 1]], TT[g[None, None, :, 5], leaf[..., 2], leaf[..., 3]]], -1).astype(np.int8)
    root = TT[g[None, None, :, 6], m[..., 0], m[..., 1]].astype(np.int8)                                              # (B, P, F)
    pooled = root.reshape(-1, 6, 4, 6, 4, F).max(axis=(2, 4)).reshape(len(win), -1)                                    # OR over 4x4 blocks -> (B, 36F)
    return g, wa, wb, leaf, m, root, pooled
def flat_forward(x):
    acts = [x]
    for i in range(2):
        g = C2[i].argmax(1); acts.append(TT[g[None, :], acts[-1][:, W2[i][0]], acts[-1][:, W2[i][1]]].astype(np.int8))
    return acts
def margin_error(out, y):
    s = out.reshape(len(y), 10, G).sum(2).astype(np.int32); st = s[np.arange(len(y)), y][:, None]; need = s - st + MARG; need[np.arange(len(y)), y] = 0; need = np.where(need > 0, need, 0); ek = np.minimum(need >> SH, LV)
    ek[np.arange(len(y)), y] = -np.minimum(ek.sum(1), 127); return ek.astype(np.int32)[:, tag]
def upd_flat(Cm, e, a, b):
    S = np.einsum("nj,njg->jg", e, TT[AR, a[:, :, None], b[:, :, None]]); S = S - S.sum(1, keepdims=True) // 16; return np.clip(Cm - np.sign(S), -CLAMP, CLAMP).astype(np.int32)
def down_flat(e, Cold, ia, ib, a, b, n_prev):
    g = Cold.argmax(1); dA = TT[g[None, :], 1, b] - TT[g[None, :], 0, b]; dB = TT[g[None, :], a, 1] - TT[g[None, :], a, 0]; flat = np.arange(len(e))[:, None] * n_prev
    r = np.bincount((flat + ia[None, :]).ravel(), weights=(e * dA).ravel(), minlength=len(e) * n_prev) + np.bincount((flat + ib[None, :]).ravel(), weights=(e * dB).ravel(), minlength=len(e) * n_prev)
    return np.clip(np.round(r), -LV, LV).reshape(len(e), n_prev).astype(np.int32)
def tree_update(node, e, a, b):                                                                                          # e, a, b: (B, P, F) for gate `node`; counters shared over batch and positions
    global C1
    if FREEZE: return
    Q = np.zeros((F, 2, 2), np.int64)
    for ia in (0, 1):
        for ib in (0, 1): Q[:, ia, ib] = ((e * ((a == ia) & (b == ib))).sum(axis=(0, 1)))
    S = np.einsum("fab,gab->fg", Q, TT.astype(np.int64)); S = S - S.sum(1, keepdims=True) // 16; C1[:, node, :] = np.clip(C1[:, node, :] - np.sign(S), -CLAMP, CLAMP)
def deriv(g, a, b): return TT[g, 1, b] - TT[g, 0, b], TT[g, a, 1] - TT[g, a, 0]
Ptr, Pte = bits(xtr), bits(xte); t0 = time.time()
def evaluate(n=10000):
    out = []
    for i in range(0, n, 500):
        win = windows(Pte[i:i + 500]); pooled = conv_forward(win)[-1]; out.append(flat_forward(pooled)[2].reshape(-1, 10, G).sum(2))
    sc = np.concatenate(out).astype(np.float32); yy = yte[:n]; CLs = np.array([0, 2, 4, 6]); mk = np.isin(yy, CLs); s6 = sc[:, 6] - np.delete(sc, 6, 1).max(1); y6 = yy == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(y6[o]); ap = ((tp / np.arange(1, len(o) + 1)) * y6[o]).sum() / y6.sum()
    return (sc.argmax(1) == yy).mean(), (CLs[sc[mk][:, CLs].argmax(1)] == yy[mk]).mean(), (sc.argmax(1)[y6] == 6).mean(), ap
for ep in range(EPOCHS):
    perm = rs.permutation(len(xtr))[:NIMG]
    for k in range(0, len(perm) - BATCH + 1, BATCH):
        idx = perm[k:k + BATCH]; y = ytr[idx]; win = windows(Ptr[idx])
        g, wa, wb, leaf, m, root, pooled = conv_forward(win); acts = flat_forward(pooled); e = margin_error(acts[2], y)
        Cold = [c.copy() for c in C2]
        for i in (1, 0):
            ia, ib = W2[i]; a = acts[i][:, ia]; b = acts[i][:, ib]; C2[i] = upd_flat(C2[i], e, a, b)
            e = down_flat(e, Cold[i], ia, ib, a, b, sizes[i])                                                          # (B, 36F) error at the pooled bits
        ep_ = e.reshape(-1, 6, 6, F); er = np.repeat(np.repeat(ep_, 4, axis=1), 4, axis=2).reshape(-1, NP, F)            # to every position of the block
        er = np.where(((er > 0) & (root == 1)) | ((er < 0) & (root == 0)), er, 0)                                         # only positions that can move the OR in the wanted direction
        m0, m1 = m[..., 0], m[..., 1]; dA, dB = deriv(g[None, None, :, 6], m0, m1); e_m0 = np.clip(er * dA, -LV, LV); e_m1 = np.clip(er * dB, -LV, LV)
        tree_update(6, er, m0, m1)
        for q, (mn, cn0, cn1, em) in enumerate(((4, 0, 1, e_m0), (5, 2, 3, e_m1))):
            a_, b_ = leaf[..., cn0], leaf[..., cn1]; dA2, dB2 = deriv(g[None, None, :, mn], a_, b_); tree_update(mn, em, a_, b_)
            e_l0, e_l1 = np.clip(em * dA2, -LV, LV), np.clip(em * dB2, -LV, LV)
            for lf, el in ((cn0, e_l0), (cn1, e_l1)): tree_update(lf, el, wa[..., lf], wb[..., lf])
    _w = windows(Pte[:300]); _g, _a, _b, _l, _m, _r, _p = conv_forward(_w); print('   diag: root bits on %.3f | pooled bits on %.3f | tree gate histogram of node 6 %s | distinct gates used per node %s' % (_r.mean(), _p.mean(), np.bincount(C1[:, 6].argmax(1), minlength=16), [len(set(C1[:, n].argmax(1))) for n in range(7)]))
    r = evaluate(); print("[%4.0fs] epoch %d: test acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f" % (time.time() - t0, ep + 1, *r), flush=True)
