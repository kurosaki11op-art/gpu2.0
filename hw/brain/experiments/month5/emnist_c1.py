"""25 Oct 2026, SIMULATED, EMNIST-balanced (47 classes: digits, upper- and lower-case letters, 28x28), one seed. Many-class test of MEM-C1 (difference-only, pruned, quantised counting table) on L's own detector code (stride 1, pool 4, 4,608 bits).
STEP=1: load, take NTR training and NTE test images (stratified random), fit the detectors on 12,000 unlabelled images, encode, cache.
STEP=2: for K in 10, 24, 47 classes: train L's counting table (CortexSlow, margin updates), centre each row on its median (lossless), prune the small differences, quantise to b bits (global scale, or one scale per row at 8 bits per row read), report accuracy and bits read per decision against the dense b-bit table (kept entries cost ceil(log2 K) bits for the class index + b bits for the code; every active row also costs an 8-bit pointer)."""
import os, sys, gzip, time
import numpy as np
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features
from cortex_slow import CortexSlow
E = lambda k, d: type(d)(os.environ.get(k, d))
STEP, NTR, NTE = E("STEP", 1), E("NTR", 40000), E("NTE", 10000)
D = "/tmp/emnist_bal"; SAVE = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/emnist_codes.npz"
rd = lambda f, off: np.frombuffer(gzip.open(os.path.join(D, "emnist-balanced-" + f)).read(), np.uint8, offset=off)
t0 = time.time()
if STEP == 1:
    xtr, ytr = rd("train-images-idx3-ubyte.gz", 16).reshape(-1, 784), rd("train-labels-idx1-ubyte.gz", 8).astype(np.int64); xte, yte = rd("test-images-idx3-ubyte.gz", 16).reshape(-1, 784), rd("test-labels-idx1-ubyte.gz", 8).astype(np.int64)
    rs = np.random.RandomState(0); itr = rs.permutation(len(xtr))[:NTR]; ite = rs.permutation(len(xte))[:NTE]; xtr, ytr, xte, yte = xtr[itr], ytr[itr], xte[ite], yte[ite]
    print("EMNIST balanced: %d train, %d test, %d classes" % (len(xtr), len(xte), len(set(ytr.tolist()))), flush=True)
    fes = [Features(32, thr=c, pool=4).fit(xtr[:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)]).astype(np.uint8)
    ctr = enc(xtr); print("[%4.0fs] train encoded, %.0f active bits per image" % (time.time() - t0, ctr.sum(1).mean()), flush=True); cte = enc(xte); np.savez(SAVE, ctr=ctr, ytr=ytr, cte=cte, yte=yte); print("[%4.0fs] saved" % (time.time() - t0))
else:
    z = np.load(SAVE); ctr, ytr, cte, yte = z["ctr"], z["ytr"], z["cte"], z["yte"]; act = cte[:2000].sum(1).mean(); Xte = cte.astype(np.float32)
    print("active bits per image %.0f" % act, flush=True)
    for K in (10, 24, 47):
        tr = ytr < K; te = yte < K; m = CortexSlow(ctr.shape[1], n_cls=K, ch=500, K=5, night_stop=2, daydream=1, seed=1); o = np.random.RandomState(100).permutation(tr.sum()); m.stage(ctr[tr][o], ytr[tr][o]); W = m.S.T.astype(np.float64)
        X = Xte[te]; y = yte[te]; acc = lambda S: (S.argmax(1) == y).mean(); Wc = W - np.median(W, axis=1, keepdims=True)
        print("\n=== K = %d classes (%d train, %d test images): dense full-precision table accuracy %.4f; centred rows %.4f; non-zero differences %.1f%% ===" % (K, tr.sum(), te.sum(), acc(X @ W.astype(np.float32)), acc(X @ Wc.astype(np.float32)), 100 * (Wc != 0).mean()), flush=True)
        ib = int(np.ceil(np.log2(K))); print("%-4s %-7s %-6s | %-8s | %-14s %-14s %-7s | %-10s" % ("bits", "scale", "kept", "acc", "bits read", "dense b-bit", "ratio", "table KB"))
        for b in (2, 3, 4):
            q = (1 << (b - 1)) - 1
            for scale_mode in ("global", "row"):
                for keep in (1.0, 0.3, 0.1, 0.05):
                    thr = np.quantile(np.abs(Wc[Wc != 0]), 1 - keep) if keep < 1 else 0; M = np.where(np.abs(Wc) >= thr, Wc, 0.0)
                    if scale_mode == "global": Q = np.round(M / (np.abs(M).max() / q)).clip(-q, q); deq = Q
                    else: sc = np.abs(M).max(1, keepdims=True) / q + 1e-12; Q = np.round(M / sc).clip(-q, q); deq = Q * sc
                    kept = (Q != 0); rows_kept = (X[:2000] @ kept.sum(1)).mean(); bits_read = rows_kept * (ib + b) + act * (8 + (8 if scale_mode == "row" else 0)); dense = act * K * b
                    print("%-4d %-7s %-6.2f | %-8.4f | %-14.0f %-14.0f %-7.2f | %-10.1f" % (b, scale_mode, keep, acc(X @ deq.astype(np.float32)), bits_read, dense, dense / bits_read, (kept.sum() * (ib + b) + W.shape[0] * 8) / 8 / 1024), flush=True)
