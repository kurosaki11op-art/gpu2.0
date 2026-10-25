"""25 Oct 2026, SIMULATED, MNIST, hard-gate integer learner (as bool_hardint.py) in a STAGED setting: classes 0-4, then 5-9 (class-incremental, no stored images).
LOCAL=1 : every layer has its own class readout (popcount of the nodes tagged with each class) and corrects only its own errors; no error crosses layers (the user's 'each layer checks and fixes its own errors').
LOCAL=0 : end-to-end: error from the output layer is passed down through truth-table derivatives.
GROW=1  : neurogenesis: before a stage, every existing node is frozen; new nodes are added to every layer (HID per layer, 100 per new class at the output) and only the new nodes learn; new nodes may read any earlier node.
GROW=0  : all nodes exist from the start and all keep learning (overwriting).
DREAM=1 : stage 2 also trains on 'dreams' of old classes: bits drawn from each old class's stored per-bit rates (a counting statistic), 30% of each batch.
env: LOCAL GROW DREAM EPOCHS HID BATCH LV CLAMP SEED"""
import os, time
import numpy as np
E = lambda k, d: type(d)(os.environ.get(k, d))
LOCAL, GROW, DREAM, EPOCHS, HID, BATCH, LV, CLAMP, SEED, STEP = E("LOCAL", 1), E("GROW", 1), E("DREAM", 0), E("EPOCHS", 4), E("HID", 250), E("BATCH", 1000), E("LV", 15), E("CLAMP", 1000), E("SEED", 0), 1
DLEVEL, SEEN2, GATE, GATEQ = E("DLEVEL", 0), E("SEEN2", 0), E("GATE", 0), E("GATEQ", 10)
rs = np.random.RandomState(SEED); GO = 100
z = np.load("/tmp/mnistdata/mnist.npz"); xtr = z["x_train"].reshape(-1, 784); ytr = z["y_train"].astype(np.int64); xte = z["x_test"].reshape(-1, 784); yte = z["y_test"].astype(np.int64)
bits = lambda x: np.concatenate([x > 85, x > 170], 1).astype(np.int8); Xtr, Xte = bits(xtr), bits(xte); NIN = Xtr.shape[1]
TT = np.array([[[(g >> (2 * a + b)) & 1 for b in (0, 1)] for a in (0, 1)] for g in range(16)], np.int32)
class Layer: pass
layers = [Layer() for _ in range(3)]
for L in layers: L.ia = L.ib = np.zeros(0, int); L.C = np.zeros((0, 16), np.int32); L.tag = np.zeros(0, int); L.frozen = np.zeros(0, bool)
def add(i, n, classes, out=False):
    L = layers[i]; n_prev = NIN if i == 0 else len(layers[i - 1].tag); C = np.zeros((n, 16), np.int32); C[:, 12] = 5
    tag = np.repeat(classes, GO) if out else rs.choice(classes, n)
    L.ia = np.concatenate([L.ia, rs.randint(0, n_prev, n)]); L.ib = np.concatenate([L.ib, rs.randint(0, n_prev, n)]); L.C = np.concatenate([L.C, C]); L.tag = np.concatenate([L.tag, tag]); L.frozen = np.concatenate([L.frozen, np.zeros(n, bool)])
def build(classes):
    add(0, HID, classes); add(1, HID, classes); add(2, GO * len(classes), classes, True)
def forward(X):
    acts = [X]; gates = []
    for L in layers:
        g = L.C.argmax(1); gates.append(g); a = acts[-1][:, L.ia]; b = acts[-1][:, L.ib]; acts.append(TT[g[None, :], a, b].astype(np.int8))
    return acts, gates
def class_scores(out, tag, seen):
    s = np.full((len(out), 10), -1e9); 
    for c in seen: s[:, c] = out[:, tag == c].sum(1) if (tag == c).any() else -1e9
    return s
def evaluate(seen, test_classes):
    acts = np.concatenate([forward(Xte[i:i + 5000])[0][3] for i in range(0, len(Xte), 5000)]); s = class_scores(acts, layers[2].tag, seen); p = s.argmax(1); r = {}
    for name, cl in test_classes.items(): m = np.isin(yte, cl); r[name] = (p[m] == yte[m]).mean()
    return r
def err_from(out, tag, y, seen):
    s = class_scores(out, tag, seen); tau = max(1.0, len(tag) / len(seen) / 10); s = s / tau; p = np.exp(s - s.max(1, keepdims=True)); p /= p.sum(1, keepdims=True)
    d = p - np.eye(10)[y]; return np.round(d / (np.abs(d).max() + 1e-12) * LV).astype(np.int32)[:, tag]
def update(i, e, a, b):
    L = layers[i]; S = np.einsum("nj,njg->jg", e, TT[np.arange(16)[None, None, :], a[:, :, None], b[:, :, None]]); S = S - S.sum(1, keepdims=True) // 16
    step = -STEP * np.sign(S); step[L.frozen] = 0; L.C = np.clip(L.C + step, -CLAMP, CLAMP).astype(np.int32)

DTYPE = os.environ.get("DREAMTYPE", "indep"); NPOOL = 3000
def make_pool(classes):
    """class-conditional dreams from counted statistics only (no stored images): indep = per-bit rates; mix = 10 prototypes per class (rates + weights); ctx = bit given left, up and lower-threshold-plane bits (8 contexts per bit)"""
    pool = {}
    for c in classes:
        D = Xtr[ytr == c].astype(np.float32)
        if DTYPE == "indep":
            r = (D.sum(0) + 1) / (len(D) + 2); pool[c] = (rs.rand(NPOOL, NIN) < r).astype(np.int8)
        elif DTYPE == "mix":
            K = 10; cen = D[rs.choice(len(D), K, replace=False)]
            for _ in range(8):
                a = (D @ cen.T - 0.5 * (cen ** 2).sum(1)[None]).argmax(1); cen = np.stack([D[a == k].mean(0) if (a == k).any() else cen[k] for k in range(K)])
            a = (D @ cen.T - 0.5 * (cen ** 2).sum(1)[None]).argmax(1); R = np.stack([(D[a == k].sum(0) + 1) / ((a == k).sum() + 2) for k in range(K)]); w = np.bincount(a, minlength=K) / len(a)
            kk = rs.choice(K, NPOOL, p=w); pool[c] = (rs.rand(NPOOL, NIN) < R[kk]).astype(np.int8)
        else:
            Dp = D.reshape(-1, 2, 28, 28).astype(np.int8); cnt = np.zeros((2, 28, 28, 8)); tot = np.zeros((2, 28, 28, 8))
            def ctxs(P, pl, y, x):
                l = P[:, pl, y, x - 1] if x > 0 else 0; u = P[:, pl, y - 1, x] if y > 0 else 0; lo = P[:, 0, y, x] if pl == 1 else 0; return l + 2 * u + 4 * lo
            for pl in (0, 1):
                for y in range(28):
                    for x in range(28):
                        cx = np.asarray(ctxs(Dp, pl, y, x)) * np.ones(len(Dp), np.int64); cx = cx.astype(np.int64); cnt[pl, y, x] = np.bincount(cx, weights=Dp[:, pl, y, x], minlength=8); tot[pl, y, x] = np.bincount(cx, minlength=8)
            T = (cnt + 0.5) / (tot + 1.0); out = np.zeros((NPOOL, 2, 28, 28), np.int8)
            for pl in (0, 1):
                for y in range(28):
                    for x in range(28):
                        cx = (np.asarray(ctxs(out, pl, y, x)) * np.ones(NPOOL, np.int64)).astype(np.int64); out[:, pl, y, x] = (rs.rand(NPOOL) < T[pl, y, x][cx])
            pool[c] = out.reshape(NPOOL, NIN)
    return pool
def train_stage(Xs, ys, seen, rates=None, old=()):
    n_batches = len(Xs) // BATCH
    for ep in range(EPOCHS):
        perm = rs.permutation(len(Xs))
        for k in range(n_batches):
            idx = perm[k * BATCH:(k + 1) * BATCH]; X = Xs[idx]; y = ys[idx]
            if DREAM and len(old):                                                                           # dreams of old classes replace 30% of the batch
                nd = int(0.3 * BATCH); yd = rs.choice(old, nd); Xd = np.stack([rates[c][rs.randint(NPOOL)] for c in yd]); X = np.concatenate([X[:BATCH - nd], Xd]); y = np.concatenate([y[:BATCH - nd], yd])
            acts, gates = forward(X)
            e = err_from(acts[3], layers[2].tag, y, seen)
            for i in (2, 1, 0):
                L = layers[i]
                if LOCAL and i < 2: e = err_from(acts[i + 1], L.tag, y, seen)                               # each layer's own readout and own error
                a = acts[i][:, L.ia]; b = acts[i][:, L.ib]; update(i, e, a, b)
                if not LOCAL and i > 0:
                    g = gates[i]; dA = TT[g[None, :], 1, b] - TT[g[None, :], 0, b]; dB = TT[g[None, :], a, 1] - TT[g[None, :], a, 0]; n_prev = len(acts[i][0]); flat = np.arange(len(X))[:, None] * n_prev
                    err = np.bincount((flat + L.ia[None, :]).ravel(), weights=(e * dA).ravel(), minlength=len(X) * n_prev) + np.bincount((flat + L.ib[None, :]).ravel(), weights=(e * dB).ravel(), minlength=len(X) * n_prev)
                    e = np.clip(np.round(err), -LV, LV).reshape(len(X), n_prev).astype(np.int32)

def make_pool_feat(A, y, classes):
    """feature-level dreams: bits of the first gate layer's output sampled from per-class counted statistics (rates, or 10 prototypes per class)"""
    pool = {}
    for c in classes:
        D = A[y == c].astype(np.float32)
        if DTYPE == "indep":
            r = (D.sum(0) + 1) / (len(D) + 2); pool[c] = (rs.rand(NPOOL, D.shape[1]) < r).astype(np.int8)
        else:
            K = 10; cen = D[rs.choice(len(D), K, replace=False)]
            for _ in range(8):
                a = (D @ cen.T - 0.5 * (cen ** 2).sum(1)[None]).argmax(1); cen = np.stack([D[a == k].mean(0) if (a == k).any() else cen[k] for k in range(K)])
            a = (D @ cen.T - 0.5 * (cen ** 2).sum(1)[None]).argmax(1); R = np.stack([(D[a == k].sum(0) + 1) / ((a == k).sum() + 2) for k in range(K)]); w = np.bincount(a, minlength=K) / len(a)
            kk = rs.choice(K, NPOOL, p=w); pool[c] = (rs.rand(NPOOL, D.shape[1]) < R[kk]).astype(np.int8)
    return pool
def forward_from(bits, start):
    acts = [None, bits]; gates = [None]
    for L in layers[start:]:
        g = L.C.argmax(1); gates.append(g); a = acts[-1][:, L.ia]; b = acts[-1][:, L.ib]; acts.append(TT[g[None, :], a, b].astype(np.int8))
    return acts, gates
def train_stage_feat(Xs, ys, seen, fpool=None, old=()):
    n_batches = len(Xs) // BATCH
    for ep in range(EPOCHS):
        perm = rs.permutation(len(Xs))
        for k in range(n_batches):
            idx = perm[k * BATCH:(k + 1) * BATCH]; X = Xs[idx]; y = ys[idx]; nd = int(0.3 * BATCH) if (DREAM and len(old)) else 0
            acts, gates = forward(X[:BATCH - nd]); y = y[:BATCH - nd]
            if nd:
                yd = rs.choice(old, nd); Fd = np.stack([fpool[c][rs.randint(NPOOL)] for c in yd]); ad, gd = forward_from(Fd, 1)
                acts = [None] + [np.concatenate([acts[i], ad[i]]) for i in (1, 2, 3)]; gates = [gates[0]] + [np.concatenate([gates[i]], 0) for i in (1, 2)]; y = np.concatenate([y, yd])
            e = err_from(acts[3], layers[2].tag, y, seen)
            for i in (2, 1):
                L = layers[i]; a = acts[i][:, L.ia]; b = acts[i][:, L.ib]; update(i, e, a, b)
                if i > 1:
                    g = L.C.argmax(1); dA = TT[g[None, :], 1, b] - TT[g[None, :], 0, b]; dB = TT[g[None, :], a, 1] - TT[g[None, :], a, 0]; n_prev = len(acts[i][0]); flat = np.arange(len(y))[:, None] * n_prev
                    err = np.bincount((flat + L.ia[None, :]).ravel(), weights=(e * dA).ravel(), minlength=len(y) * n_prev) + np.bincount((flat + L.ib[None, :]).ravel(), weights=(e * dB).ravel(), minlength=len(y) * n_prev)
                    e = np.clip(np.round(err), -LV, LV).reshape(len(y), n_prev).astype(np.int32)
t0 = time.time(); S1, S2 = [0, 1, 2, 3, 4], [5, 6, 7, 8, 9]
if GROW: build(S1)
else: build(list(range(10)))
m1 = np.isin(ytr, S1)
train_stage(Xtr[m1], ytr[m1], S1)
r1 = evaluate(S1, {"stage1 classes": S1}); print("after stage 1: accuracy on classes 0-4 (among 0-4) %.4f | %.0fs" % (r1["stage1 classes"], time.time() - t0), flush=True)
if GROW:
    for L in layers: L.frozen[:] = True
    if DLEVEL: add(1, HID, S2); add(2, GO * 5, S2, True)                                                    # layer 0 stays frozen and does not grow
    else: add(0, HID, S2); add(1, HID, S2); add(2, GO * 5, S2, True)
m2 = np.isin(ytr, S2)
seen2 = S2 if SEEN2 else list(range(10))
if DLEVEL:
    A1 = np.concatenate([forward(Xtr[m1][i:i + 5000])[0][1] for i in range(0, m1.sum(), 5000)]); fpool = make_pool_feat(A1, ytr[m1], S1) if DREAM else None
    train_stage_feat(Xtr[m2], ytr[m2], seen2, fpool, S1)
else:
    rates = make_pool(S1) if DREAM else None
    train_stage(Xtr[m2], ytr[m2], seen2, rates, S1)
r2 = evaluate(list(range(10)), {"old 0-4": S1, "new 5-9": S2, "all": list(range(10))})
_a = np.concatenate([forward(Xte[i:i + 5000])[0][3] for i in range(0, len(Xte), 5000)]); _p = class_scores(_a, layers[2].tag, list(range(10))).argmax(1); _o = np.isin(yte, S1); _n = np.isin(yte, S2)
print("DIAG old images: predicted old-and-right %.3f, old-but-wrong-old %.3f, predicted NEW %.3f | new images: predicted new-right %.3f, new-but-wrong-new %.3f, predicted OLD %.3f" % ((_p[_o] == yte[_o]).mean(), (np.isin(_p[_o], S1) & (_p[_o] != yte[_o])).mean(), np.isin(_p[_o], S2).mean(), (_p[_n] == yte[_n]).mean(), (np.isin(_p[_n], S2) & (_p[_n] != yte[_n])).mean(), np.isin(_p[_n], S1).mean()))
print("mean group score (of 100) on old / new images: old groups %.1f / %.1f, new groups %.1f / %.1f" % (_a[_o][:, np.isin(layers[2].tag, S1)].mean() * 100, _a[_n][:, np.isin(layers[2].tag, S1)].mean() * 100, _a[_o][:, np.isin(layers[2].tag, S2)].mean() * 100, _a[_n][:, np.isin(layers[2].tag, S2)].mean() * 100))

if GATE:
    from scipy.stats import rankdata
    oldn = np.isin(layers[2].tag, S1); newn = ~oldn
    def grp(X):
        out = np.concatenate([forward(X[i:i + 5000])[0][3] for i in range(0, len(X), 5000)]); return np.stack([out[:, layers[2].tag == c].sum(1) for c in range(10) if (layers[2].tag == c).any()], 1).astype(float), [c for c in range(10) if (layers[2].tag == c).any()]
    gtr, cls_ = grp(Xtr[m1]); gte, _ = grp(Xte); cls_ = np.array(cls_); io = np.isin(cls_, S1); mo_tr = gtr[:, io].max(1); T = np.percentile(mo_tr, GATEQ); mo = gte[:, io].max(1); old_te = np.isin(yte, S1)
    r = rankdata(np.concatenate([mo[old_te], mo[~old_te]])); auc = (r[:old_te.sum()].sum() - old_te.sum() * (old_te.sum() + 1) / 2) / (old_te.sum() * (~old_te).sum())
    pred = np.where(mo >= T, cls_[io][gte[:, io].argmax(1)], cls_[~io][gte[:, ~io].argmax(1)])
    print("GATE (max raw old-class group score, threshold = %dth percentile of stage-1 training images): AUROC old-vs-new %.3f | old acc %.4f | new acc %.4f | all %.4f" % (GATEQ, auc, (pred[old_te] == yte[old_te]).mean(), (pred[~old_te] == yte[~old_te]).mean(), (pred == yte).mean()), flush=True)
print("LOCAL=%d GROW=%d DREAM=%d TYPE=%s | after stage 2 among all 10 classes: old %.4f | new %.4f | all %.4f | %.0fs" % (LOCAL, GROW, DREAM, DTYPE, r2["old 0-4"], r2["new 5-9"], r2["all"], time.time() - t0), flush=True)
