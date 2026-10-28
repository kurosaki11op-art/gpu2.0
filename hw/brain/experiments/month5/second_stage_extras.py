"""28 Oct 2026, SIMULATED accuracy, ESTIMATED energy. NEXT TEST after the routed second pass (routed_second_pass.md). Two questions at the same route share and with cost beside each number:
 (1) BETTER ROUTER: which images should take the stronger second pass? Label-free routers using only the first (shipped) pass:
     margin       : smallest top-1 minus top-2 margin first (the router used so far),
     cluster-aware: margin, with a bonus for images whose top-1 or top-2 class is T-shirt, Pullover, Coat or Shirt (the confusable group),
     class-relative: margin divided by the typical margin of the predicted class (first 20,000 train images), so classes that are usually unsure are routed more.
 (2) CLAUSES IN THE SECOND PASS: second pass = the 64-informative front end (installed alone) plus the kept clause bits (the existing clause state over L's shipped code + raw pixels; the clauses are evaluated only for routed images).
The first pass is L as shipped on every image. Second pass scores replace the first for routed images (z-scored, as in the routed tests). Cost (cost_frontier.py model): shipped energy + route share x (second-pass front end + table reads + clause reads). Clause extra per routed image estimated from best_version_energy_tiles.md: about 41 nJ for 2,000 clauses and 83 nJ for 4,000 (keyed reads plus the extra table rows).
env: SEED."""
import os, sys, time, copy
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, ytr, xte, yte, train_table, CL, Features, ctr, cte
from numba import njit, prange
E_ = lambda k, d: type(d)(os.environ.get(k, d)); SEED = E_("SEED", 0); POOLF = 128; KSEL = 64; K = 10; t0 = time.time()
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"
def sram(kb): return 10.0 if kb <= 8 else 20.0 if kb <= 32 else 20.0 + 80.0 * min(1.0, (kb - 32) / 992)
fe_det = 576 * 0.23 / 1000; tab = lambda bits, act: act * (sram(bits * 10 / 1024) + 1.0) / 1000; E_ship = 4 * 32 * fe_det + tab(4608, 589)
CH = [50, 150, ("on", 8), ("off", 8)]
def mi_per_detector(codes, y, F):
    N = len(y); n1 = np.stack([codes[y == c].sum(0) for c in range(K)]).astype(np.float64); nc = np.bincount(y, minlength=K).astype(np.float64); n1t = n1.sum(0); mi = np.zeros(codes.shape[1])
    for c in range(K):
        for b in (0, 1):
            nb = (n1[c] if b else nc[c] - n1[c]); nbt = (n1t if b else N - n1t); pcb = (nb + 0.5) / (N + 1); mi += pcb * np.log(pcb / ((nc[c] / N) * ((nbt + 0.5) / (N + 1))))
    return mi.reshape(36, F).sum(0)
fes = []
for c in CH:
    fe = Features(POOLF, seed=SEED, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]); sub = xtr[:20000]
    a = np.concatenate([fe.encode(sub[i:i + 2000]) for i in range(0, len(sub), 2000)]).astype(np.uint8); idx = np.sort(np.argsort(-mi_per_detector(a, ytr[:20000], POOLF))[:KSEL])
    f2 = copy.copy(fe); f2.cnt = fe.cnt[idx].copy(); f2.F = len(idx); fes.append(f2)
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for i in range(0, len(x), 2000)]) for g in fes], 1).astype(np.uint8)
A, B = enc(xtr), enc(xte); act = B.sum(1).mean(); print("stage-2 code encoded [%.0fs]" % (time.time() - t0), flush=True)
W0 = train_table(ctr, ytr); S0 = cte.astype(np.int32) @ W0; S1 = B.astype(np.int32) @ train_table(A, ytr)
# clause bits over L's shipped code + raw pixels (existing seed-0 state, 8,000 clauses)
def bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
Ctr, Cte = np.concatenate([ctr, bits(xtr)], 1), np.concatenate([cte, bits(xte)], 1); NB = Ctr.shape[1]; st = np.load(SP + "tm_faithful_state_both.npz"); inc_list, inc_n = st["inc_list"], st["inc_n"]
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
ftr, fte = fire(Ctr), fire(Cte); Wr = train_table(ftr[:20000], ytr[:20000]); order = np.argsort(-(Wr.max(1) - Wr.min(1))); print("clauses fired [%.0fs]" % (time.time() - t0), flush=True)
S1c = {}
for N in (2000, 4000):
    keep = order[:N]; S1c[N] = np.concatenate([B, fte[:, keep]], 1).astype(np.int32) @ train_table(np.concatenate([A, ftr[:, keep]], 1), ytr)
def metrics(S):
    p = S.argmax(1); mk = np.isin(yte, CL); s6 = S[:, 6] - np.delete(S, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    return (p == yte).mean(), (CL[S[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap
zs = lambda S: (S - S.mean(1, keepdims=True)) / (S.std() + 1e-9)
srt = np.sort(S0, 1); marg = (srt[:, -1] - srt[:, -2]).astype(np.float64); top2 = np.argsort(-S0, 1)[:, :2]; incl = np.isin(top2, CL).any(1)
Str = ctr[:20000].astype(np.int32) @ W0; st_ = np.sort(Str, 1); mtr = (st_[:, -1] - st_[:, -2]).astype(np.float64); ptr = Str.argmax(1); typ = np.array([mtr[ptr == c].mean() if (ptr == c).any() else mtr.mean() for c in range(K)])
routers = {"margin": marg, "cluster-aware": marg - 0.6 * marg.std() * incl, "class-relative": marg / typ[S0.argmax(1)]}
second = 4 * KSEL * fe_det + tab(A.shape[1], act); clause_extra = {2000: 41.0, 4000: 83.0}
print("first pass alone: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | est. %.1f nJ" % (metrics(S0) + (E_ship,)), flush=True)
print("second pass alone: stage-2 %.4f | stage-2 + 2000 clauses %.4f | + 4000 clauses %.4f (accuracy, every image)" % (metrics(S1)[0], metrics(S1c[2000])[0], metrics(S1c[4000])[0]), flush=True)
for rn, score in routers.items():
    for r in (0.1, 0.2, 0.3):
        route = score <= np.quantile(score, r)
        for sn, S2, ex in (("stage-2", S1, 0.0), ("stage-2 + 2000 clauses", S1c[2000], clause_extra[2000]), ("stage-2 + 4000 clauses", S1c[4000], clause_extra[4000])):
            S = np.where(route[:, None], zs(S2), zs(S0)); cost = E_ship + r * (second + ex)
            print("RESULT router %-14s %3.0f%% routed, second pass %-24s acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | est. %.1f nJ (%.2f x L)" % ((rn, 100 * r, sn) + metrics(S) + (cost, cost / E_ship)), flush=True)
