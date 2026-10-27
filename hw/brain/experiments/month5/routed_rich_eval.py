"""27 Oct 2026, SIMULATED. ROUTED RICH FRONT END (learned from the failures: gains from more channels, two-level codes and clauses overlap because they re-read the same features, and routing was the only thing that kept a gain at a fraction of the cost). L's shipped code and table decide first; only the images the shipped table is least sure about (smallest top-1 minus top-2 margin) are sent through the richer front end (7 channels: pixel thresholds 32,80,128,176,224 + on8 + off8, two-level output) and re-scored by the richer table. Everything else keeps the shipped answer and never runs the extra channels. Final score for routed images = the richer table's score (z-scored, as in the routed clause test), others = shipped table's.
Cost (ESTIMATED, the cost_frontier.py model): shipped energy for every image + route share x (front end of the channels NOT already computed + richer table reads); the on8 and off8 channels are shared with the shipped code and computed once. Reported for route shares 0.2, 0.3, 0.5, 1.0 and for two richer tables (levels 1,2 and 1,3)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ytr, yte, ctr, cte, train_table, CL
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"
def sram(kb): return 10.0 if kb <= 8 else 20.0 if kb <= 32 else 20.0 + 80.0 * min(1.0, (kb - 32) / 992)
fe_ch = 576 * 32 * 0.23 / 1000; tab = lambda bits, act: act * (sram(bits * 10 / 1024) + 1.0) / 1000
E_ship = 4 * fe_ch + tab(4608, 589)
chs = ["t32", "t80", "t128", "t176", "t224", "on8", "off8"]; cn = {c: np.load(SP + "cnt_%s.npz" % c) for c in chs}
def metrics(S):
    p = S.argmax(1); mk = np.isin(yte, CL); s6 = S[:, 6] - np.delete(S, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    return (p == yte).mean(), (CL[S[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap
zs = lambda S: (S - S.mean(1, keepdims=True)) / (S.std() + 1e-9)
S0 = cte.astype(np.int32) @ train_table(ctr, ytr); srt = np.sort(S0, 1); marg = srt[:, -1] - srt[:, -2]
print("shipped alone: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | est. %.1f nJ" % (metrics(S0) + (E_ship,)), flush=True)
for levels in ((1, 2), (1, 3)):
    code = lambda w: np.concatenate([np.concatenate([(cn[c]["ab"[w]] >= t) for t in levels], 1) for c in chs], 1).astype(np.uint8)
    A, B = code(0), code(1); S1 = B.astype(np.int32) @ train_table(A, ytr); act = B.sum(1).mean(); extra_fe = 5 * fe_ch                    # five threshold channels beyond the shared on8/off8
    full = 7 * fe_ch + tab(A.shape[1], act)
    print("rich alone (levels %s, every image): acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | est. %.1f nJ" % ((levels,) + metrics(S1) + (full,)), flush=True)
    for r in (0.2, 0.3, 0.5, 1.0):
        route = marg <= np.quantile(marg, r); S = np.where(route[:, None], zs(S1), zs(S0)); cost = E_ship + r * (extra_fe + tab(A.shape[1], act))
        print("RESULT routed rich (levels %s), %.0f%% of images: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f | est. %.1f nJ (%.2f x L)" % ((levels, 100 * r) + metrics(S) + (cost, cost / E_ship)), flush=True)
