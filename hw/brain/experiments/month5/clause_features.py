"""25 Oct 2026, SIMULATED, Fashion-MNIST. L-Deep v3: the clause layer as the deeper layer. The trained Tsetlin-style clauses (400 per class, 4,000 hidden units, each an AND of a few bit-literals of L's code, learned by local feedback only, saved by tm_faithful.py) are evaluated on every image; which clauses fire is a new sparse code; L's counting table (margin-trained, one row per class) reads it.
Compared with the clause learner's own vote and with L's code alone. Uses the saved state of the last tm_faithful.py run (C=400, s=3, about 3.5 epochs)."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, report, CL
from numba import njit, prange
CK = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/tm_faithful_state.npz"
z = np.load(CK); inc_list, inc_n = z["inc_list"], z["inc_n"]; NCL = len(inc_n); C = NCL // 10; NB = ctr.shape[1]; print("clauses per class %d, total %d, mean included literals %.1f, epochs of training %d" % (C, NCL, inc_n.mean(), int(z["ep"])), flush=True)
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
print("[%3.0fs] clause outputs: active clauses per image %.0f of %d (L's code: %.0f active bits of %d)" % (time.time() - t0, ftr.sum(1).mean(), NCL, ctr[:2000].sum(1).mean(), NB), flush=True)
pol = np.where(np.arange(NCL) % C % 2 == 0, 1, -1); cls = np.arange(NCL) // C
vote = np.zeros((len(fte), 10), np.float32)
for c in range(10): vote[:, c] = (fte[:, cls == c] * pol[cls == c]).sum(1)
report("clause learner's own vote", vote)
W = train_table(ftr, ytr); report("L's counting table on clause firing bits (4,000 bits)", fte.astype(np.int32) @ W)
W = train_table(np.concatenate([ctr, ftr], 1), ytr); report("L's counting table on L's code + clause bits", np.concatenate([cte, fte], 1).astype(np.int32) @ W)
W = train_table(ctr, ytr); report("reference: L's counting table on L's code alone", cte.astype(np.int32) @ W)
