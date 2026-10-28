"""28 Oct 2026, SIMULATED. (Part 2 of deep_fix_test.py, see the log: hard-only training did NOT help.) Residual Deep: stage 2 keeps L's scores S1 and ADDS a clause correction (F @ Wcl, int8 weights times 2^k), trained by softmax regression on the training images with cross-fitted S1 (so S1 is not over-confident on the training set). Drops the second scan of the 4,608 code rows. Why does L Deep break 2.1% of images it should keep right, and does training its stage-2 table on the images it will actually see (the least-sure ones) fix it? Same clauses, same kept 2,000, same routing rule (L's margin, 20th percentile of the test margins) as the shipped build;
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

import torch
torch.manual_seed(0); torch.set_num_threads(4)
# cross-fitted S1 on the training set
S1tr = np.zeros((len(ytr), 10), np.float32)
for a, b in ((hA, hB), (hB, hA)): S1tr[b] = ctr[b].astype(np.int32) @ train_table(ctr[a], ytr[a])
S1te = S_L.astype(np.float32); Ftr = torch.tensor(ftr[:, keep].astype(np.float32)); Fte = torch.tensor(fte[:, keep].astype(np.float32)); S1trt = torch.tensor(S1tr); ytrt = torch.tensor(ytr)
mtrain = mtr
def run(tag, k, sel_share, steps=300, tau=400.0, wd=1e-4):
    idx = np.arange(len(ytr)) if sel_share >= 1 else np.nonzero(mtrain <= np.quantile(mtrain, sel_share))[0]; it = torch.tensor(idx)
    W = torch.zeros(Ftr.shape[1], 10, requires_grad=True); opt = torch.optim.Adam([W], lr=2.0)
    for s in range(steps):
        opt.zero_grad(); loss = torch.nn.functional.cross_entropy((S1trt[it] + (Ftr[it] @ W) * 2 ** k) / tau, ytrt[it]) + wd * (W ** 2).mean(); loss.backward(); opt.step()
    Wq = torch.clamp(torch.round(W.detach()), -127, 127)
    Sf = torch.tensor(S1te) + (Fte @ Wq) * 2 ** k; p2 = Sf.argmax(1).numpy(); fin = np.where(route, p2, pl)
    fixes = (route & (pl != yte) & (p2 == yte)).sum() / len(yte); breaks = (route & (pl == yte) & (p2 != yte)).sum() / len(yte)
    print("%-40s routed acc %.4f | total %.4f | fixes %.2f%% breaks %.2f%% | weight range %d..%d [%4.0fs]" % (tag, (p2[route] == yte[route]).mean(), (fin == yte).mean(), 100 * fixes, 100 * breaks, Wq.min(), Wq.max(), time.time() - t0), flush=True)
for k in (0, 2, 4):
    run("residual, shift %d, all training images" % k, k, 1.0)
for k in (2, 4):
    run("residual, shift %d, hardest 40%%" % k, k, 0.4)
