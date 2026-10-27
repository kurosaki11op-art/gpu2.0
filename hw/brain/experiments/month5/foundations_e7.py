"""27 Oct 2026, SIMULATED. FOUNDATIONS E7: what information does the dense network use that a binary code loses? Same trained 32-filter CNN as E6 (float backprop, 20 epochs); its pooled responses are read in four ways:
 (a) float softmax readout on the real pooled responses (the CNN's own readout, retrained: reference),
 (b) float softmax readout on the BINARISED responses (one threshold per filter),
 (c) our counting table on the binarised responses (E6),
 (d) our counting table on MULTI-LEVEL (thermometer) codes: each response gives 1, 2, 3 or 4 bits (on above successive quantiles).
(b) separates 'binarisation loses information' from 'the counting readout loses information'; (d) tests whether graded information can be kept with bits and counters only."""
import os, sys, time
os.environ["ONLY"] = "none"; os.environ["F"] = "32"
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import foundations_raw as R
from shirt_new_methods_setup import ytr, yte, train_table
t0 = time.time(); rs = np.random.RandomState(0); m = R.Model("cnn", False, F=32)
for e in range(20):
    order = rs.permutation(len(R.Xtr))
    for i in range(0, len(order), R.BS): j = order[i:i + R.BS]; m.step(R.Xtr[j], ytr[j])
print("CNN float with its own readout: test acc %.4f [%.0fs]" % (m.acc(R.Xte, yte), time.time() - t0), flush=True)
pooled = lambda X: np.concatenate([m.forward(X[i:i + 1000])[1]["pool"].reshape(min(1000, len(X) - i), 169, 32) for i in range(0, len(X), 1000)])
Ptr, Pte = pooled(R.Xtr), pooled(R.Xte)
def softmax_readout(A, B, ep=8):
    Wt = np.zeros((A.shape[1], 10), np.float32); b = np.zeros(10, np.float32); opt = R.Adam(); r = np.random.RandomState(0)
    for e in range(ep):
        o = r.permutation(len(A))
        for i in range(0, len(o), 128):
            j = o[i:i + 128]; dz = (R.softmax(A[j] @ Wt + b) - np.eye(10, dtype=np.float32)[ytr[j]]) / len(j); opt("W", Wt, A[j].T @ dz); opt("b", b, dz.sum(0))
    return ((B @ Wt + b).argmax(1) == yte).mean()
flat = lambda P: P.reshape(len(P), -1)
mu = flat(Ptr).mean(0); sd = flat(Ptr).std(0) + 1e-6
print("RESULT (a) float readout on real pooled responses (standardised)        acc %.4f [%.0fs]" % (softmax_readout((flat(Ptr) - mu) / sd, (flat(Pte) - mu) / sd), time.time() - t0), flush=True)
thr = lambda q: np.quantile(Ptr[::7].reshape(-1, 32), q, axis=0)
def code(P, qs): return np.concatenate([(P > thr(q)).reshape(len(P), -1) for q in qs], 1).astype(np.uint8)
b1tr, b1te = code(Ptr, (0.7,)), code(Pte, (0.7,))
print("RESULT (b) float readout on BINARISED responses (q 0.7, %d bits)        acc %.4f [%.0fs]" % (b1tr.shape[1], softmax_readout(b1tr.astype(np.float32), b1te.astype(np.float32)), time.time() - t0), flush=True)
for qs in ((0.7,), (0.7, 0.9), (0.5, 0.75, 0.9), (0.4, 0.6, 0.8, 0.9)):
    A, B = code(Ptr, qs), code(Pte, qs); W = train_table(A, ytr)
    print("RESULT (d) our counting table, %d-level code (quantiles %s, %d bits, %.0f active): acc %.4f [%.0fs]" % (len(qs), qs, A.shape[1], B.sum(1).mean(), ((B.astype(np.int32) @ W).argmax(1) == yte).mean(), time.time() - t0), flush=True)
