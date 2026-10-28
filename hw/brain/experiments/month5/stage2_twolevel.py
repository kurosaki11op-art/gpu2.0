"""28 Oct 2026, SIMULATED accuracy, ESTIMATED energy. TWO-LEVEL OUTPUT ON THE STAGE-2 DETECTORS, routed. The second pass is the 64-informative front end (installed alone, 64 of a 128 pool per channel, seed SEED). Each detector reports per 4x4 pooled window 'won at least once' (level 1) and, as a second bit, 'won at T or more of the 16 positions' (T = 4, the best single second level on the shipped code, or levels 1,2,4). The second pass runs only on the images the shipped first pass is least sure about (margin router), so the larger table only pays on routed images. Cost (cost_frontier.py model): shipped energy + route share x (second-pass front end + reads of the larger table).
env: SEED."""
import os, sys, time, copy
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, ytr, xte, yte, train_table, CL, Features, ctr, cte
from feature_layer import patches, support_filter, binarize
E_ = lambda k, d: type(d)(os.environ.get(k, d)); SEED = E_("SEED", 0); POOLF = 128; KSEL = 64; K = 10; t0 = time.time()
def sram(kb): return 10.0 if kb <= 8 else 20.0 if kb <= 32 else 20.0 + 80.0 * min(1.0, (kb - 32) / 992)
fe_det = 576 * 0.23 / 1000; tab = lambda bits, act: act * (sram(bits * 10 / 1024) + 1.0) / 1000; E_ship = 4 * 32 * fe_det + tab(4608, 589)
CH = [50, 150, ("on", 8), ("off", 8)]
def mi_per_detector(codes, y, F):
    N = len(y); n1 = np.stack([codes[y == c].sum(0) for c in range(K)]).astype(np.float64); nc = np.bincount(y, minlength=K).astype(np.float64); n1t = n1.sum(0); mi = np.zeros(codes.shape[1])
    for c in range(K):
        for b in (0, 1):
            nb = (n1[c] if b else nc[c] - n1[c]); nbt = (n1t if b else N - n1t); pcb = (nb + 0.5) / (N + 1); mi += pcb * np.log(pcb / ((nc[c] / N) * ((nbt + 0.5) / (N + 1))))
    return mi.reshape(36, F).sum(0)
def counts(fe, x):                                                                                    # (B, 36*F) number of positions in each 4x4 window where each detector won
    p, n = patches(support_filter(binarize(x, fe.thr), fe.support)); B = len(x); W = fe.winners(p.reshape(-1, p.shape[-1])).reshape(B, n, n); on = (p.sum(2) >= fe.min_on).reshape(B, n, n); m = n // fe.pool
    cnt = np.zeros((B, m, m, fe.F), np.uint8)
    for di in range(fe.pool):
        for dj in range(fe.pool):
            ww = W[:, di:m * fe.pool:fe.pool, dj:m * fe.pool:fe.pool]; oo = on[:, di:m * fe.pool:fe.pool, dj:m * fe.pool:fe.pool]; bi, ii, jj = np.nonzero(oo); cnt[bi, ii, jj, ww[bi, ii, jj]] += 1
    return cnt.reshape(B, -1)
fes = []
for c in CH:
    fe = Features(POOLF, seed=SEED, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]); sub = xtr[:20000]
    a = np.concatenate([fe.encode(sub[i:i + 2000]) for i in range(0, len(sub), 2000)]).astype(np.uint8); idx = np.sort(np.argsort(-mi_per_detector(a, ytr[:20000], POOLF))[:KSEL])
    f2 = copy.copy(fe); f2.cnt = fe.cnt[idx].copy(); f2.F = len(idx); fes.append(f2); print("  channel %s installed [%.0fs]" % (c, time.time() - t0), flush=True)
cn = lambda x: np.concatenate([np.concatenate([counts(g, x[i:i + 2000]) for i in range(0, len(x), 2000)]) for g in fes], 1)
Ctr, Cte = cn(xtr), cn(xte); print("counts encoded [%.0fs]" % (time.time() - t0), flush=True)
def metrics(S):
    p = S.argmax(1); mk = np.isin(yte, CL); s6 = S[:, 6] - np.delete(S, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    return (p == yte).mean(), (CL[S[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap
zs = lambda S: (S - S.mean(1, keepdims=True)) / (S.std() + 1e-9)
S0 = cte.astype(np.int32) @ train_table(ctr, ytr); srt = np.sort(S0, 1); marg = srt[:, -1] - srt[:, -2]
print("first pass alone: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | est. %.1f nJ" % (metrics(S0) + (E_ship,)), flush=True)
for levels in ((1,), (1, 4), (1, 2, 4)):
    A, B = [np.concatenate([(M >= t) for t in levels], 1).astype(np.uint8) for M in (Ctr, Cte)]; act = B.sum(1).mean(); S1 = B.astype(np.int32) @ train_table(A, ytr); second = 4 * KSEL * fe_det + tab(A.shape[1], act)
    print("second pass alone, levels %s (%d bits, %.0f active, every image): acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | est. %.1f nJ" % ((levels, A.shape[1], act) + metrics(S1) + (second,)), flush=True)
    for r in (0.1, 0.2, 0.3):
        route = marg <= np.quantile(marg, r); S = np.where(route[:, None], zs(S1), zs(S0)); cost = E_ship + r * second
        print("RESULT levels %-9s routed %.0f%%: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | est. %.1f nJ (%.2f x L)" % ((str(levels), 100 * r) + metrics(S) + (cost, cost / E_ship)), flush=True)
