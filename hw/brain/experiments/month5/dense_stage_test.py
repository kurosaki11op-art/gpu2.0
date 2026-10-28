"""28 Oct 2026, SIMULATED accuracy, ESTIMATED energy. Would a small multiplier-based (int8 dense) stage on raw pixels, run only on the routed images, beat L Deep per joule?
Routed set = same rule as L Deep (margin of L's table <= its 20th percentile). Dense stage trained on the training set; accuracy measured on the routed test images and on the whole test set.
Energy: MACs at 0.2 pJ (int8 multiply-add, 45 nm Horowitz reference) + every weight read once from SRAM at the project's constants (10 pJ per 64-bit word up to 8 KB, about 22 pJ per word at 50 KB), x the routed share 0.2 for the per-image average. All ESTIMATED.
Compared with L alone (88.85%, about 30 nJ) and L Deep (89.73%, about 49 nJ average per image)."""
import sys, time
sys.argv = ["x", "/tmp/fashion"]
sys.path.insert(0, "/home/user/gpu2.0/hw/brain/experiments/month5")
import numpy as np
from shirt_new_methods_setup import ctr, cte, xtr, xte, ytr, yte, train_table
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
t0 = time.time(); W = train_table(ctr, ytr); S = cte.astype(np.int32) @ W; srt = np.sort(S, 1); marg = srt[:, -1] - srt[:, -2]; T = np.floor(np.quantile(marg, 0.2)); route = marg <= T
pl = S.argmax(1); print("L alone %.4f; routed %.1f%%; accuracy of L on routed images %.4f, on unrouted %.4f [%.0fs]" % ((pl == yte).mean(), 100 * route.mean(), (pl[route] == yte[route]).mean(), (pl[~route] == yte[~route]).mean(), time.time() - t0), flush=True)
A, B = xtr / 255.0, xte / 255.0; E_MAC = 0.2e-3
def energy(params, macs): words = params / 8; per = 10 if params <= 8192 else (20 if params <= 32768 else 22); return macs * E_MAC + words * per * 1e-3   # nJ per routed image
def report(tag, p, params, macs):
    tot = np.where(route, p, pl); e = energy(params, macs)
    print("%-28s routed acc %.4f | total acc %.4f | dense stage %.1f nJ per routed image = %.1f nJ per image on average | params %d" % (tag, (p[route] == yte[route]).mean(), (tot == yte).mean(), e, 0.2 * e, params), flush=True)
lr = LogisticRegression(max_iter=150, C=1.0).fit(A, ytr); report("logistic (784x10)", lr.predict(B), 784 * 10, 784 * 10)
for h in (32, 64, 128):
    m = MLPClassifier((h,), max_iter=30, random_state=0).fit(A, ytr); report("MLP 784-%d-10" % h, m.predict(B), 784 * h + h * 10, 784 * h + h * 10)
