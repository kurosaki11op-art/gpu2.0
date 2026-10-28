"""28 Oct 2026, SIMULATED accuracy, ESTIMATED energy. L DEEP COST FRONTIER: how many of the 8,000 clauses (ranked by table use) are worth keeping? For N kept clauses: accuracy of the two-stage integer pipeline (routed 30% by the shipped table's margin), Shirt AP, clauses firing, literal checks per routed image (counted with early exit), and the energy per image from counted operations (ESTIMATED, 45 nm constants as in l_deep_build.md: literal read 0.22 of a 21.5 pJ word read, header read 0.375 of a 12 pJ word, row reads 1.25 words at about 21 to 23 pJ, stage 1 and the encoder 34 nJ). Env: SEED (0 or 1) picks the saved clause state."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, xtr, xte, CL
from numba import njit, prange
SEED = int(os.environ.get("SEED", 0)); t0 = time.time()
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"
z = np.load(SP + ("tm_faithful_state_both.npz" if SEED == 0 else "tm_faithful_state_both_s1.npz")); inc_list, inc_n = z["inc_list"], z["inc_n"]
def _bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
IN_TR = np.concatenate([ctr, _bits(xtr)], 1).astype(np.uint8); IN_TE = np.concatenate([cte, _bits(xte)], 1).astype(np.uint8); NB = IN_TR.shape[1]
@njit(parallel=True)
def fire_count(X, inc_list, inc_n, nb):
    out = np.zeros((len(X), len(inc_n)), np.uint8); chk = np.zeros(len(X), np.int64)
    for i in prange(len(X)):
        n_l = 0
        for cl in range(len(inc_n)):
            n = inc_n[cl]
            if n == 0: continue
            ok = 1
            for t in range(n):
                lit = inc_list[cl, t]; n_l += 1
                if lit < nb:
                    if X[i, lit] == 0: ok = 0; break
                else:
                    if X[i, lit - nb] == 1: ok = 0; break
            out[i, cl] = ok
        chk[i] = n_l
    return out, chk
def fire(X, il, inn):
    o, c = zip(*[fire_count(X[i:i + 5000], il, inn, NB) for i in range(0, len(X), 5000)]); return np.concatenate(o), np.concatenate(c)
ftr, _ = fire(IN_TR, inc_list, inc_n); fte, _ = fire(IN_TE, inc_list, inc_n)
W = train_table(ftr[:20000], ytr[:20000]); use = W.max(1) - W.min(1); order = np.argsort(-use)
W_L = train_table(ctr, ytr); S_L = cte.astype(np.int32) @ W_L; srt = np.sort(S_L, 1); marg = srt[:, -1] - srt[:, -2]; route = marg <= np.quantile(marg, 0.3)
def zs(S): return (S - S.mean(1, keepdims=True)) / (S.std() + 1e-9)
def metrics(sc):
    p = sc.argmax(1); s6 = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum(); return (p == yte).mean(), ap
print("seed %d. L alone: acc %.4f, Shirt AP %.3f. Routed share 30%%." % ((SEED,) + metrics(zs(S_L))), flush=True)
print("%-7s %8s %9s %9s %12s %10s %12s %12s" % ("kept N", "acc", "Shirt AP", "firing", "lit checks", "stage-2 nJ", "system nJ", "acc gain"))
for N in (0, 250, 500, 1000, 2000, 3000, 4000, 6000):
    if N == 0: sc = zs(S_L); fires = 0; chk = 0.0
    else:
        keep = order[:N]; il, inn = inc_list[keep], inc_n[keep]; ft = ftr[:, keep]; fe, ck = fire(IN_TE[route], il, inn); fe_all = fte[:, keep]
        A = np.concatenate([ctr, ft], 1); B = np.concatenate([cte, fe_all], 1); W2 = train_table(A, ytr); S2 = B.astype(np.int32) @ W2; sc = np.where(route[:, None], zs(S2), zs(S_L)); fires = fe_all[route].sum(1).mean(); chk = ck.mean()
    a, ap = metrics(sc)
    stage2 = 0.0 if N == 0 else (631 * 1.25 * 21 + chk * 0.22 * 21.5 + N * 0.375 * 12 + fires * 1.25 * 23) / 1000
    print("%-7d %8.4f %9.3f %9.0f %12.0f %10.0f %12.0f %+11.2f" % (N, a, ap, fires, chk, stage2, 34 + 0.3 * stage2, 100 * (a - metrics(zs(S_L))[0])), flush=True)
