"""27 Oct 2026, SIMULATED. WITHIN-BUDGET COMBINATION: routed clause layer on top of the two-level output code. The clause state is the existing one (seed 0: 800 clauses per class, literals over L's shipped 4,608-bit code + 1,568 raw pixel bits). L's shipped code is exactly the level-1 bits of the two-level code (checked), so the clauses fire unchanged. The counting table reads the two-level code (levels 1 and 4, 9,216 bits) plus the kept clause bits. Reported: table on the two-level code alone, plus the best N clauses on every image, and routed (only the 30% of images with the smallest table margin evaluate the clauses). Cost from the consistent model of cost_frontier.py (ESTIMATED): table part uses the active bits and table size; clause reads from best_version_energy_tiles.md scaled by N and routing."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, xte, ytr, yte, train_table, CL
from numba import njit, prange
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"; t0 = time.time()
chs = ["t50", "t150", "on8", "off8"]                                                                  # the shipped four channels
cn = {c: np.load(SP + "cnt_%s.npz" % c) for c in chs}
code14 = lambda w: np.concatenate([np.concatenate([(cn[c]["ab"[w]] >= 1), (cn[c]["ab"[w]] >= 4)], 1) for c in chs], 1).astype(np.uint8)
ship = lambda w: np.concatenate([(cn[c]["ab"[w]] >= 1) for c in chs], 1).astype(np.uint8)
def bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
Atr, Ate = code14(0), code14(1); Ctr, Cte = np.concatenate([ship(0), bits(xtr)], 1), np.concatenate([ship(1), bits(xte)], 1); NB = Ctr.shape[1]
z = np.load(SP + "shirt_cache.npz"); print("level-1 bits equal L's shipped code: %s [%.0fs]" % (bool((ship(0) == z["ctr"]).all()), time.time() - t0), flush=True)
st = np.load(SP + "tm_faithful_state_both.npz"); inc_list, inc_n = st["inc_list"], st["inc_n"]; NCL = len(inc_n)
@njit(parallel=True)
def fire_all(X, inc_list, inc_n, nb):
    out = np.zeros((len(X), len(inc_n)), np.uint8)
    for i in prange(len(X)):
        for cl in range(len(inc_n)):
            n = inc_n[cl]
            if n == 0: continue
            ok = 1
            for t in range(n):
                lit = inc_list[cl, t]
                if lit < nb:
                    if X[i, lit] == 0: ok = 0; break
                elif X[i, lit - nb] == 1: ok = 0; break
            out[i, cl] = ok
    return out
fire = lambda X: np.concatenate([fire_all(X[i:i + 5000], inc_list, inc_n, NB) for i in range(0, len(X), 5000)])
ftr, fte = fire(Ctr), fire(Cte); print("clauses fired [%.0fs]" % (time.time() - t0), flush=True)
W0 = train_table(Atr, ytr); S0 = Ate.astype(np.int32) @ W0; srt = np.sort(S0, 1); marg = srt[:, -1] - srt[:, -2]; route = marg <= np.quantile(marg, 0.3)
Wr = train_table(ftr[:20000], ytr[:20000]); order = np.argsort(-(Wr.max(1) - Wr.min(1)))
def metrics(S):
    p = S.argmax(1); mk = np.isin(yte, CL); s6 = S[:, 6] - np.delete(S, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    return (p == yte).mean(), (CL[S[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap
zs = lambda S: (S - S.mean(1, keepdims=True)) / (S.std() + 1e-9)
print("RESULT two-level code alone (levels 1,4): acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f (%.0f active)" % (metrics(S0) + (Ate.sum(1).mean(),)), flush=True)
for N in (2000, 4000):
    keep = order[:N]; A = np.concatenate([Atr, ftr[:, keep]], 1); B = np.concatenate([Ate, fte[:, keep]], 1); W = train_table(A, ytr); S = B.astype(np.int32) @ W; rt = np.where(route[:, None], zs(S), zs(S0))
    print("RESULT + %d clauses, every image: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f (%.0f clauses fire) || routed 30%%: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f [%.0fs]" % ((N,) + metrics(S) + (fte[:, keep].sum(1).mean(),) + metrics(rt) + (time.time() - t0,)), flush=True)
