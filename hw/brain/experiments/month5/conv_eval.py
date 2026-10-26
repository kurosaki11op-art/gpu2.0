"""26 Oct 2026, SIMULATED. L + convolutional (weight-shared) clauses: fire bits of tm_conv.py clauses appended to L's code, one counting table, clauses ranked by table use on 20,000 images. env: WIN, C (same as training), NS."""
import os, sys, time
os.environ.setdefault("BUDGET", "0")
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tm_conv as M
from shirt_new_methods_setup import ctr, cte, ytr, yte, train_table, CL
z = np.load(M.CK); inc_list, inc_n = z["inc_list"], z["inc_n"]; t0 = time.time()
ftr = M.fire_bits(M.G, inc_list, inc_n); fte = M.fire_bits(M.Gt, inc_list, inc_n); print("[%4.0fs] %d conv clauses, %.0f fire per image (epochs %d)" % (time.time() - t0, len(inc_n), ftr.sum(1).mean(), int(z["ep"])), flush=True)
W = train_table(ftr[:20000], ytr[:20000]); order = np.argsort(-(W.max(1) - W.min(1)))
def metrics(sc):
    p = sc.argmax(1); mk = np.isin(yte, CL); s6 = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    return (p == yte).mean(), (CL[sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap
print("L alone                  acc %.4f | cluster %.4f | recall %.3f | AP %.3f" % metrics(cte.astype(np.int32) @ train_table(ctr, ytr)))
for N in [int(v) for v in os.environ.get("NS", "1000,2000,4000").split(",")]:
    keep = order[:min(N, len(inc_n))]; A = np.concatenate([ctr, ftr[:, keep]], 1); B = np.concatenate([cte, fte[:, keep]], 1); Wc = train_table(A, ytr)
    print("L + %-5d conv clauses    acc %.4f | cluster %.4f | recall %.3f | AP %.3f | %.0f fire per image" % ((N,) + metrics(B.astype(np.int32) @ Wc) + (fte[:, keep].sum(1).mean(),)), flush=True)
