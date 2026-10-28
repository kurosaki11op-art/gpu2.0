"""28 Oct 2026, SIMULATED. (Part 3 of deep_fix_test.py.) Specialist clauses: a second clause layer (state tm_faithful_state_both_hard.npz, trained by tm_faithful.py with HARDQ=0.4 on the 40% of training images L is least sure about) is ADDED to the shipped 2,000 clauses; the stage-2 table is retrained on code + both clause sets. Reports fixes / breaks against L on the routed images. Why does L Deep break 2.1% of images it should keep right, and does training its stage-2 table on the images it will actually see (the least-sure ones) fix it? Same clauses, same kept 2,000, same routing rule (L's margin, 20th percentile of the test margins) as the shipped build;
only the training set of the stage-2 table changes. Variants: shipped (all 60,000 training images); hard-only (training images whose L margin is in the lowest share h, margins taken from a 2-fold cross-fitted L so they are not inflated by training on the same images); all + hard repeated.
Reports accuracy on the routed test images, total accuracy, and how many images Deep fixes / breaks against L (on the routed set)."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, xtr, xte
from numba import njit, prange
t0 = time.time(); STATE = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/tm_faithful_state_both.npz"
z = np.load(STATE); inc_list, inc_n = z["inc_list"], z["inc_n"]
def _bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
IN_TR = np.concatenate([ctr, _bits(xtr)], 1).astype(np.uint8); IN_TE = np.concatenate([cte, _bits(xte)], 1).astype(np.uint8); NB = IN_TR.shape[1]
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
fire = lambda X: np.concatenate([fire_all(X[i:i + 5000], inc_list, inc_n, NB) for i in range(0, len(X), 5000)])
ftr, fte = fire(IN_TR), fire(IN_TE)
W = train_table(ftr[:20000], ytr[:20000]); use = W.max(1) - W.min(1); keep = np.argsort(-use)[:2000]
W_L = train_table(ctr, ytr); S_L = cte.astype(np.int32) @ W_L; srt = np.sort(S_L, 1); marg = srt[:, -1] - srt[:, -2]; T = int(np.floor(np.quantile(marg, 0.2))); route = marg <= T; pl = S_L.argmax(1)
A = np.concatenate([ctr, ftr[:, keep]], 1); B = np.concatenate([cte, fte[:, keep]], 1)
# cross-fitted L margins on the training set (each half scored by a table trained on the other half)
rs = np.random.RandomState(5); perm = rs.permutation(len(ytr)); hA, hB = perm[: len(perm) // 2], perm[len(perm) // 2:]; mtr = np.zeros(len(ytr))
for a, b in ((hA, hB), (hB, hA)):
    Wh = train_table(ctr[a], ytr[a]); s = np.sort(ctr[b].astype(np.int32) @ Wh, 1); mtr[b] = s[:, -1] - s[:, -2]
print("[%4.0fs] prepared; L alone %.4f, routed %.1f%%, L on routed %.4f" % (time.time() - t0, (pl == yte).mean(), 100 * route.mean(), (pl[route] == yte[route]).mean()), flush=True)

st = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/tm_faithful_state_both_hard.npz"); il2, in2 = st["inc_list"], st["inc_n"]
f2tr = np.concatenate([fire_all(IN_TR[i:i + 5000], il2, in2, NB) for i in range(0, len(IN_TR), 5000)]); f2te = np.concatenate([fire_all(IN_TE[i:i + 5000], il2, in2, NB) for i in range(0, len(IN_TE), 5000)])
print("[%4.0fs] specialist clauses: %d, mean literals %.1f, fire rate %.3f" % (time.time() - t0, len(in2), in2.mean(), f2te.mean()), flush=True)
def evaluate(tag, Atr, Bte):
    Wc = train_table(Atr, ytr); S2 = Bte.astype(np.int32) @ Wc; p2 = S2.argmax(1); fin = np.where(route, p2, pl)
    fixes = (route & (pl != yte) & (p2 == yte)).sum() / len(yte); breaks = (route & (pl == yte) & (p2 != yte)).sum() / len(yte)
    print("%-44s routed acc %.4f | total %.4f | all-image acc %.4f | fixes %.2f%% breaks %.2f%% [%4.0fs]" % (tag, (p2[route] == yte[route]).mean(), (fin == yte).mean(), (p2 == yte).mean(), 100 * fixes, 100 * breaks, time.time() - t0), flush=True)
evaluate("shipped (code + 2,000 clauses)", A, B)
use2 = np.abs(train_table(f2tr[:20000], ytr[:20000])).max(1)
for n2 in (1000, 3000):
    k2 = np.argsort(-use2)[:n2]; evaluate("code + 2,000 + %d specialist clauses" % n2, np.concatenate([A, f2tr[:, k2]], 1), np.concatenate([B, f2te[:, k2]], 1))
k2 = np.argsort(-use2)[:2000]; evaluate("code + 2,000 specialist clauses only", np.concatenate([ctr, _bits(xtr), f2tr[:, k2]], 1), np.concatenate([cte, _bits(xte), f2te[:, k2]], 1))
