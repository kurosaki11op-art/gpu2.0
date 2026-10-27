"""27 Oct 2026, SIMULATED. FOUNDATIONS E6: is the front end (feature extraction) what limits L? Train the 32-filter shared-weight CNN (float, backprop, 20 epochs) on raw pixels, then DISCARD its readout: take its pooled filter responses, binarise them (a response is 'on' when above the per-filter quantile Q of training responses, giving a sparse binary code like L's), and train OUR counting table (L's margin rule, integers only) on that code. Compare: L's own Hebbian code + table (88.85), the CNN with its float readout (91.3), and the CNN code + our table. Also reports sparsity and the same table on a random-filter code (filters not learned).
env: Q quantile, EP epochs."""
import os, sys, time
os.environ["ONLY"] = "none"; os.environ["F"] = "32"
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import foundations_raw as R
from shirt_new_methods_setup import ytr, yte, train_table, ctr, cte
EP = int(os.environ.get("EP", 20)); t0 = time.time(); rs = np.random.RandomState(0)
m = R.Model("cnn", False, F=32)
for e in range(EP):
    order = rs.permutation(len(R.Xtr))
    for i in range(0, len(order), R.BS): j = order[i:i + R.BS]; m.step(R.Xtr[j], ytr[j])
print("CNN float with its own readout: test acc %.4f [%.0fs]" % (m.acc(R.Xte, yte), time.time() - t0), flush=True)
def pooled(model, X): return np.concatenate([model.forward(X[i:i + 1000])[1]["pool"].reshape(min(1000, len(X) - i), -1) for i in range(0, len(X), 1000)])
Ptr, Pte = pooled(m, R.Xtr), pooled(m, R.Xte)
rnd = R.Model("cnn", False, F=32); Rtr, Rte = pooled(rnd, R.Xtr), pooled(rnd, R.Xte)                  # untrained (random) filters, same pipeline
for q in (0.5, 0.7, 0.8, 0.9):
    for nm, A, B in (("learned filters", Ptr, Pte), ("random filters", Rtr, Rte)):
        F = A.shape[1] // 169; thr = np.quantile(A.reshape(len(A), 169, F).reshape(-1, F)[::7], q, axis=0)                  # per-filter quantile
        bt = (A.reshape(len(A), 169, F) > thr).reshape(len(A), -1).astype(np.uint8); be = (B.reshape(len(B), 169, F) > thr).reshape(len(B), -1).astype(np.uint8)
        W = train_table(bt, ytr); acc = ((be.astype(np.int32) @ W).argmax(1) == yte).mean(); print("RESULT %-16s code on above-quantile %.1f (%.0f active of %d bits): our counting table acc %.4f [%.0fs]" % (nm, q, be.sum(1).mean(), be.shape[1], acc, time.time() - t0), flush=True)
print("reference: L's own Hebbian code + the same table: %.4f" % ((cte.astype(np.int32) @ train_table(ctr, ytr)).argmax(1) == yte).mean(), flush=True)
