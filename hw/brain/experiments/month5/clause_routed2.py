"""25 Oct 2026, SIMULATED, Fashion-MNIST, one seed. Best-accuracy version of the clause layer with routing, memory-safe. Uses the saved clause state (any number of clauses per class), computes which clauses fire in chunks, ranks all clauses by how much a table trained on a 20,000-image subset uses them (spread of their row across classes), keeps the best N, trains the tables on all 60,000 training images and reports: L alone, L + N clauses on every image, and routed (only the 30% of images with the smallest L margin evaluate the clauses).
env: STATE (npz path), NS (comma list of clause counts to keep)"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, CL
from numba import njit, prange
E = lambda k, d: type(d)(os.environ.get(k, d))
CK = E("STATE", "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/tm_faithful_state.npz"); NS = [int(v) for v in E("NS", "8000,16000").split(",")]
z = np.load(CK); inc_list, inc_n = z["inc_list"], z["inc_n"]; NCL = len(inc_n); NB = ctr.shape[1]; t0 = time.time()
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
                else:
                    if X[i, lit - nb] == 1: ok = 0; break
            out[i, cl] = ok
    return out
def fire(X): return np.concatenate([fire_all(X[i:i + 5000], inc_list, inc_n, NB) for i in range(0, len(X), 5000)])
if E("INPUT", "code") == "deep":                                                                     # layer 2 reads L's code + raw bits + the firing bits of the frozen layer-1 bank
    from shirt_new_methods_setup import xtr, xte
    def _bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
    _z1 = np.load(E("STATE1", "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/tm_faithful_state_both.npz")); _il, _in = _z1["inc_list"], _z1["inc_n"]
    _b1, _b2 = np.concatenate([ctr, _bits(xtr)], 1).astype(np.uint8), np.concatenate([cte, _bits(xte)], 1).astype(np.uint8); _nb = _b1.shape[1]
    _f1 = lambda B: np.concatenate([fire_all(B[i:i + 5000], _il, _in, _nb) for i in range(0, len(B), 5000)])
    CTR_IN, CTE_IN = np.concatenate([_b1, _f1(_b1)], 1), np.concatenate([_b2, _f1(_b2)], 1); NB = CTR_IN.shape[1]; L1TR, L1TE = _f1(_b1), _f1(_b2)
else:
    L1TR = L1TE = None
if E("INPUT", "code") == "both":
    from shirt_new_methods_setup import xtr, xte
    def _bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
    CTR_IN, CTE_IN = np.concatenate([ctr, _bits(xtr)], 1), np.concatenate([cte, _bits(xte)], 1); NB = CTR_IN.shape[1]
elif E("INPUT", "code") != "deep": CTR_IN, CTE_IN = ctr, cte
ftr = fire(CTR_IN.astype(np.uint8)); fte = fire(CTE_IN.astype(np.uint8)); del CTR_IN, CTE_IN; print("[%4.0fs] %d clauses, %.0f fire per image (epochs trained %d)" % (time.time() - t0, NCL, ftr.sum(1).mean(), int(z["ep"])), flush=True)
L1KEEP = np.arange(0, 0) if int(E('L1N', 0)) == 0 else np.arange(int(E('L1N', 0)))
W = train_table(ftr[:20000], ytr[:20000]); use = W.max(1) - W.min(1); order = np.argsort(-use); print("[%4.0fs] clauses ranked by table use" % (time.time() - t0), flush=True)
def z_(S): return (S - S.mean(1, keepdims=True)) / (S.std() + 1e-9)
def metrics(sc):
    p = sc.argmax(1); mk = np.isin(yte, CL); s6 = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    return (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap
W_L = train_table(ctr, ytr); S_L = cte.astype(np.int32) @ W_L; srt = np.sort(S_L, 1); marg = srt[:, -1] - srt[:, -2]; route = marg <= np.quantile(marg, 0.3)
print("%-40s acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f" % (("L alone",) + metrics(S_L)), flush=True)
for N in NS:
    keep = order[:min(N, NCL)]; A = np.concatenate([ctr, ftr[:, keep]] + ([L1TR[:, L1KEEP]] if L1TR is not None else []), 1); B = np.concatenate([cte, fte[:, keep]] + ([L1TE[:, L1KEEP]] if L1TR is not None else []), 1); W_LC = train_table(A, ytr); S_LC = B.astype(np.int32) @ W_LC; del A
    routed = np.where(route[:, None], z_(S_LC), z_(S_L)); print("[%4.0fs] N=%-6d every image: acc %.4f | cluster %.4f | recall %.3f | Shirt AP %.3f  ||  routed (30%% of images): acc %.4f | cluster %.4f | recall %.3f | Shirt AP %.3f  | %.0f clauses fire per image" % ((time.time() - t0, N) + metrics(S_LC) + metrics(routed) + (fte[:, keep].sum(1).mean(),)), flush=True)
