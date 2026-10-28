"""28 Oct 2026, SIMULATED accuracy, ESTIMATED energy. HYBRID STUDY (founder's decision of 28 Oct 2026: multiplication and matrices are allowed where a test shows they pay). First pass: L as shipped (matrix-free) on every image. Second pass: a small convolutional network with 8, 16 or 32 shared 3x3 filters (float32 training in numpy, weights then quantised to int8; activations kept in float in this simulation, so the int8 accuracy is an approximation), run ONLY on the images the first pass is least sure about (margin router); for those images the CNN's answer replaces L's. The CNN is a SIMULATED reference model trained here, not a measured GPU result.
Cost (ESTIMATED, 45 nm constants as in cost_frontier.py): int8 CNN = multiply-adds x 0.23 pJ + weight words x SRAM read for its size + activation words (written once, read once) x 10 pJ + pixel reads; hybrid energy = shipped L energy for every image + routed share x CNN energy."""
import os, sys, time
os.environ["ONLY"] = "none"; os.environ["F"] = "32"
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import foundations_raw as R
from shirt_new_methods_setup import ytr, yte, ctr, cte, train_table, CL
t0 = time.time()
def sram(kb): return 10.0 if kb <= 8 else 20.0 if kb <= 32 else 20.0 + 80.0 * min(1.0, (kb - 32) / 992)
def cnn_energy(F):
    macs = 26 * 26 * 9 * F + 13 * 13 * F * 10; w_bytes = 9 * F + 13 * 13 * F * 10; w_words = w_bytes / 8; act_words = 26 * 26 * F / 8 * 2
    return (macs * 0.23 + w_words * sram(w_bytes / 1024) + act_words * 10 + 98 * 10) / 1000, macs
E_ship = 4 * 32 * 576 * 0.23 / 1000 + 589 * (sram(4608 * 10 / 1024) + 1.0) / 1000
def metrics(p, S=None):
    mk = np.isin(yte, CL); return (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[mk] == yte[mk]).mean()
S0 = cte.astype(np.int32) @ train_table(ctr, ytr); p0 = S0.argmax(1); srt = np.sort(S0, 1); marg = srt[:, -1] - srt[:, -2]
print("first pass (L shipped) alone: acc %.4f | Shirt recall %.3f | cluster %.4f | est. %.1f nJ" % (metrics(p0) + (E_ship,)), flush=True)
def q8(W): m = np.abs(W).max() + 1e-12; return np.round(W / m * 127) / 127 * m
for F in (8, 16, 32):
    rs = np.random.RandomState(0); m = R.Model("cnn", False, F=F)
    for e in range(20):
        order = rs.permutation(len(R.Xtr))
        for i in range(0, len(order), R.BS): j = order[i:i + R.BS]; m.step(R.Xtr[j], ytr[j])
    pf = np.concatenate([m.forward(R.Xte[i:i + 1000])[0].argmax(1) for i in range(0, len(R.Xte), 1000)])
    m.Wc, m.W = q8(m.Wc), q8(m.W); p8 = np.concatenate([m.forward(R.Xte[i:i + 1000])[0].argmax(1) for i in range(0, len(R.Xte), 1000)])
    en, macs = cnn_energy(F); print("CNN %d filters: float acc %.4f | int8 weights acc %.4f | Shirt recall %.3f | %d multiply-adds | est. %.0f nJ at int8 [%.0fs]" % ((F, metrics(pf)[0]) + (metrics(p8)[0], metrics(p8)[1], macs, en, time.time() - t0)), flush=True)
    for r in (0.1, 0.2, 0.3, 0.5, 1.0):
        route = marg <= np.quantile(marg, r); p = np.where(route, p8, p0); a, sh, cl = metrics(p); cost = E_ship + r * en
        print("RESULT hybrid, CNN %2d filters, %3.0f%% routed: acc %.4f | Shirt recall %.3f | cluster %.4f | est. %.1f nJ (%.2f x L)" % (F, 100 * r, a, sh, cl, cost, cost / E_ship), flush=True)
