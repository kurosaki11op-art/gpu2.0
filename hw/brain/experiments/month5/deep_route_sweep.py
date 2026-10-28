"""28 Oct 2026, SIMULATED accuracy, ESTIMATED energy. L DEEP ROUTING SHARE: with N kept clauses, how do accuracy and system energy change with the share r of images (least sure by the shipped table's margin) sent to stage 2? Same energy model as deep_frontier.py. Env: SEED, N."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
import importlib.util
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "deep_frontier.py")).read().split("print(\"seed")[0]
exec(src)
N = int(os.environ.get("N", 2000)); keep = order[:N]; il, inn = inc_list[keep], inc_n[keep]
fe_all, ck_all = fire(IN_TE, il, inn); A = np.concatenate([ctr, ftr[:, keep]], 1); B = np.concatenate([cte, fe_all], 1); W2 = train_table(A, ytr); S2 = B.astype(np.int32) @ W2
base = metrics(zs(S_L))[0]; fires_all = fe_all.sum(1)
print("seed %d, N %d clauses kept. L alone %.4f. Routed by margin quantile r:" % (SEED, N, base)); print("%-6s %8s %10s %12s %12s %10s" % ("r", "acc", "gain", "stage-2 nJ", "system nJ", "x L (34)"))
for r in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 1.0):
    route = marg <= np.quantile(marg, r) if r > 0 else np.zeros(len(marg), bool)
    if r == 1.0: route = np.ones(len(marg), bool)
    sc = np.where(route[:, None], zs(S2), zs(S_L)); a, ap = metrics(sc)
    st2 = 0.0 if not route.any() else (631 * 1.25 * 21 + ck_all[route].mean() * 0.22 * 21.5 + N * 0.375 * 12 + fires_all[route].mean() * 1.25 * 23) / 1000
    print("%-6.1f %8.4f %+9.2f %12.0f %12.0f %10.2f" % (r, a, 100 * (a - base), st2, 34 + r * st2, (34 + r * st2) / 34), flush=True)
