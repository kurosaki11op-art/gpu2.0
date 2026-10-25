"""25 Oct 2026, SIMULATED. Counting table (CortexSlow) read in two stages (classes 0-5, then 6-9 = Shirt, Sneaker, Bag, Boot) over: L's code alone; the frozen gate layers' output bits alone; both together. Features from bool_frozen_features.py."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, CL, CortexSlow
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/frozen_feats.npz"); ftr, fte = z["ftr"], z["fte"]
def run(tag, A, B):
    t0 = time.time(); m = CortexSlow(A.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1)
    for i, st in enumerate(([0, 1, 2, 3, 4, 5], [6, 7, 8, 9])):
        sel = np.where(np.isin(ytr, st))[0]; sel = sel[np.random.RandomState(100 + i).permutation(len(sel))]; m.stage(A[sel], ytr[sel])
        if i == 0: p0 = (B.astype(np.int32) @ m.S.T.astype(np.int32))[:, :6].argmax(1); mk = yte < 6; r0 = (p0[mk] == yte[mk]).mean()
    sc = B.astype(np.int32) @ m.S.T.astype(np.int32); p = sc.argmax(1); mk = np.isin(yte, CL); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("%-34s bits %5d | after stage 1 (base, 6-way) %.4f | after stage 2: old %.4f new %.4f all %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | %.0fs" % (tag, A.shape[1], r0, (p[yte < 6] == yte[yte < 6]).mean(), (p[yte >= 6] == yte[yte >= 6]).mean(), (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap, time.time() - t0), flush=True)
run("L code only", ctr, cte)
run("frozen gate layers only", ftr, fte)
run("L code + frozen gate layers", np.concatenate([ctr, ftr], 1), np.concatenate([cte, fte], 1))
