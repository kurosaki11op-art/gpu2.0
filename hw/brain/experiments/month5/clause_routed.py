"""25 Oct 2026, SIMULATED, Fashion-MNIST, one seed. Our own method 2: ROUTED CLAUSES. The clause layer (800 clauses per class, saved state of tm_faithful.py, about 5.5 epochs) gives L's table a gain but costs about 2.7 times L's reads on EVERY image. The gain is concentrated in the confusable cluster (T-shirt, Pullover, Coat, Shirt). Routing: L's own table (on L's code alone) decides first; only images whose top class lies in the cluster (or whose top-1 minus top-2 margin is small) are sent on to evaluate the clauses and be re-scored by the table that reads L's code plus the clause bits. Everything else keeps L's answer and never touches the clause store.
Reports accuracy, cluster accuracy, Shirt AP (final scores = routed table's, scaled to unit spread), and the share of images that evaluate clauses, with the estimated energy of the clause evaluations scaled by that share (energy constants of clause_energy.py)."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, CL
from numba import njit, prange
CK = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/tm_faithful_state.npz"
z = np.load(CK); inc_list, inc_n = z["inc_list"], z["inc_n"]; NCL = len(inc_n); NB = ctr.shape[1]
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
ftr = fire_all(ctr.astype(np.uint8), inc_list, inc_n, NB); fte = fire_all(cte.astype(np.uint8), inc_list, inc_n, NB); print("clauses %d; %.0f fire per image" % (NCL, ftr.sum(1).mean()), flush=True)
W_L = train_table(ctr, ytr); W_LC = train_table(np.concatenate([ctr, ftr], 1), ytr)
S_L = cte.astype(np.int32) @ W_L; S_LC = np.concatenate([cte, fte], 1).astype(np.int32) @ W_LC
def z_(S): return (S - S.mean(1, keepdims=True)) / (S.std() + 1e-9)
def metrics(sc):
    p = sc.argmax(1); mk = np.isin(yte, CL); s6 = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    return (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), ap
print("%-46s acc %.4f | cluster %.4f | Shirt AP %.3f" % (("L alone (every image)",) + metrics(S_L))); print("%-46s acc %.4f | cluster %.4f | Shirt AP %.3f" % (("L + clauses on every image",) + metrics(S_LC)))
srt = np.sort(S_L, 1); marg = srt[:, -1] - srt[:, -2]; top = S_L.argmax(1)
for name, route in (("cluster only (top class in T-shirt/Pullover/Coat/Shirt)", np.isin(top, CL)), ("cluster, plus margin below its 20th percentile", np.isin(top, CL) | (marg <= np.quantile(marg, 0.2))), ("margin below the 30th percentile only", marg <= np.quantile(marg, 0.3)), ("margin below the 50th percentile only", marg <= np.quantile(marg, 0.5))):
    final = np.where(route[:, None], z_(S_LC), z_(S_L)); share = route.mean(); a, c, ap = metrics(final)
    print("%-46s acc %.4f | cluster %.4f | Shirt AP %.3f | images that evaluate clauses %.0f%%" % (name, a, c, ap, 100 * share))
