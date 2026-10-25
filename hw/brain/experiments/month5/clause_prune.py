"""25 Oct 2026, SIMULATED, Fashion-MNIST, one seed. Win-win tests for L-Deep v3 (clause layer read by L's counting table): cut the number of rows read per image while keeping the gain. Uses the saved 800-clause state (T 60, s 3, about 5.5 epochs).
MODE=prune : train the table on all 8,000 clause bits, rank clauses by how much the table uses them (spread of their row across classes), keep the top K (also ranked per firing: use per read), retrain, report rows read.
MODE=topk  : no retraining of clauses; for each class only the K most specific firing clauses (most included literals) report; table retrained on this sparse code.
Reference: L's code alone 88.85 / Shirt AP 0.753 / 578 rows. Success (win-win): at most about the same rows as L (about 600) with accuracy above 88.85 and Shirt AP above 0.753; (or L's code + clause code at under 1.5 times L's rows)."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, report, CL
from numba import njit, prange
MODE = os.environ.get("MODE", "prune")
CK = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/tm_faithful_state.npz"
z = np.load(CK); inc_list, inc_n = z["inc_list"], z["inc_n"]; NCL = len(inc_n); C = NCL // 10; NB = ctr.shape[1]
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
t0 = time.time(); ftr = fire_all(ctr.astype(np.uint8), inc_list, inc_n, NB); fte = fire_all(cte.astype(np.uint8), inc_list, inc_n, NB)
print("[%3.0fs] %d clauses (%d per class), %.0f fire per image" % (time.time() - t0, NCL, C, ftr.sum(1).mean()), flush=True)
def go(tag, Ftr, Fte, extra=False):
    if extra: Ftr = np.concatenate([ctr, Ftr], 1); Fte = np.concatenate([cte, Fte], 1)
    W = train_table(Ftr, ytr); sc = Fte.astype(np.int32) @ W; p = sc.argmax(1); mk = np.isin(yte, CL); s6 = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("[%3.0fs] %-52s rows read %5.0f (x%.2f of L) | acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f" % (time.time() - t0, tag, Fte.sum(1).mean(), Fte.sum(1).mean() / 578, (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap), flush=True)
if MODE == "prune":
    W = train_table(ftr, ytr); use = W.max(1) - W.min(1); rate = ftr.mean(0) + 1e-4
    for K in (500, 1000, 2000, 4000):
        for name, rank in (("by table use", use), ("by table use per read", use / rate)):
            keep = np.argsort(-rank)[:K]; go("top %d clauses %s" % (K, name), ftr[:, keep], fte[:, keep])
else:
    for k in (2, 4, 8):
        rnd = np.random.RandomState(0).rand(1, C).astype(np.float32) * 0.5
        def topk(F):
            out = np.zeros_like(F)
            for c in range(10):
                blk = F[:, c * C:(c + 1) * C].astype(np.float32); score = blk * (inc_n[c * C:(c + 1) * C][None, :].astype(np.float32) + 1 + rnd); idx = np.argpartition(-score, k, axis=1)[:, :k]
                rows = np.arange(len(F))[:, None]; out[rows, c * C + idx] = blk[rows, idx].astype(np.uint8)
            return out
        Ttr, Tte = topk(ftr), topk(fte); go("top %d most specific firing clauses per class" % k, Ttr, Tte); go("  same + L's code", Ttr, Tte, extra=True)
