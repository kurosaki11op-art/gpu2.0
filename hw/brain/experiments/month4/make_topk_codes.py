"""Finer grid with competition inside each cell (19 Oct): detectors at stride 1 (24 x 24 spots of winners, as ENC_S1), but each 4 x 4 cell keeps only its TOPK most frequent winners
(count >= MINC), instead of OR-ing all of them. Same 4,608-bit code, density near today's (stride 2, pool 2) instead of ~2x. Saves sep_{DS}_topk{TOPK}_F32.npz. usage: DATA_DIR DS TOPK [MINC]. SIMULATED."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, feature_layer
from feature_layer import Features, binarize, patches, support_filter
from cortex_core import load
D, DS, TOPK = sys.argv[1], sys.argv[2], int(sys.argv[3]); MINC = int(sys.argv[4]) if len(sys.argv) > 4 else 1
feature_layer.PS, feature_layer.ST = 5, 1
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64)
fes = [Features(32, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]


def enc(x):
    outs = []
    for fe in fes:
        res = []
        for i in range(0, len(x), 2000):
            xb = x[i:i + 2000]; p, n = patches(support_filter(binarize(xb, fe.thr), 0)); B = len(xb)
            W = fe.winners(p.reshape(-1, p.shape[-1])).reshape(B, n, n); on = (p.sum(2) >= fe.min_on).reshape(B, n, n)
            m = n // 4; code = np.zeros((B, m, m, fe.F), bool)
            for ci in range(m):
                for cj in range(m):
                    w = W[:, ci * 4:ci * 4 + 4, cj * 4:cj * 4 + 4].reshape(B, 16); o = on[:, ci * 4:ci * 4 + 4, cj * 4:cj * 4 + 4].reshape(B, 16)
                    cnt = np.zeros((B, fe.F), np.int32)
                    for q in range(16):
                        np.add.at(cnt, (np.arange(B), w[:, q]), o[:, q])
                    top = np.argsort(-cnt, 1, kind="stable")[:, :TOPK]
                    sel = np.take_along_axis(cnt, top, 1) >= MINC
                    bi, ki = np.nonzero(sel); code[bi, ci, cj, top[bi, ki]] = True
            res.append(code.reshape(B, -1))
        outs.append(np.concatenate(res, 0))
    return np.concatenate(outs, 1)


tr, te = enc(xtr), enc(xte)
np.savez_compressed(os.path.join(D, f"sep_{DS}_topk{TOPK}_F32.npz"), tr=tr, te=te); print("saved", DS, TOPK, "on bits", tr.sum(1).mean())
