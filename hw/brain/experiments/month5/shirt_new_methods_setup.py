"""Shared setup for the 24 Oct 2026 Shirt new-method tests: L's code (stride 1, pool 4, 4,608 bits) for train, test, and horizontally flipped copies, cached on disk. usage: import after sys.argv[1]=DATA_DIR"""
import os, sys, time
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features
CACHE = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/shirt_cache.npz"
D = "/tmp/fashion"
xtr, ytr, xte, yte = load(D, "fashion"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
CL = np.array([0, 2, 4, 6]); NAMES = ["T-shirt","Trouser","Pullover","Dress","Coat","Sandal","Shirt","Sneaker","Bag","Boot"]
CH = (50, 150, ("on", 8), ("off", 8))
fes = [Features(32, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)]).astype(np.uint8)
flip = lambda x: x.reshape(-1, 28, 28)[:, :, ::-1].reshape(-1, 784).copy()
if os.path.exists(CACHE):
    z = np.load(CACHE); ctr, cte, ctrf, ctef = z["ctr"], z["cte"], z["ctrf"], z["ctef"]
else:
    t0 = time.time(); ctr, cte = enc(xtr), enc(xte); ctrf, ctef = enc(flip(xtr)), enc(flip(xte)); print("encoded %.0fs" % (time.time() - t0), flush=True)
    np.savez(CACHE, ctr=ctr, cte=cte, ctrf=ctrf, ctef=ctef)

def train_table(codes, labels, seed=1):
    m = CortexSlow(codes.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=seed)
    sel = np.random.RandomState(100).permutation(len(labels)); m.stage(codes[sel], labels[sel]); return m.S.T.astype(np.int32)

def report(tag, sc):
    p = sc.argmax(1); mk = np.isin(yte, CL); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s); tp = np.cumsum(yy[o])
    ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("%-50s acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f" % (tag, (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap), flush=True)
