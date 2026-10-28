"""28 Oct 2026, SIMULATED. Does a better routing signal raise the accuracy of the L + L Deep system at the SAME routed share (so the same energy)?
Both stages are evaluated on every test image (integer scores from the RTL memory files via ldeep_ref), then each signal picks the images to route; routed images take Deep's answer, the rest L's.
Signals: (1) margin (shipped); (2) margin only when L's top class is in the confusable set {T-shirt, Pullover, Dress, Coat, Shirt}; (3) margin relative to the top score; (4) a tiny learned router (logistic regression on the margin, the top-two class pair and the two scores, cross-fitted 2-fold on the test set so every image is scored by a router that did not see it);
(5) upper bounds: route exactly the images where Deep fixes L (oracle, not realisable) and route all images (share 100%). Share swept 10 to 40%."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ldeep_ref as R
from sklearn.linear_model import LogisticRegression
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/deep_test_all.npz"); X, y = np.ascontiguousarray(z["X"], np.uint8), z["y"].astype(np.int64); n = len(y)
S1 = X[:, :R.NCODE].astype(np.int64) @ R.W1; S2 = X[:, :R.NCODE].astype(np.int64) @ R.W2 + R._fire(X, R.INC, R.INC_N, R.NB) @ R.WCL
p1, p2 = S1.argmax(1), S2.argmax(1); a1, a2 = (p1 == y), (p2 == y)
print("L alone %.4f | Deep on every image %.4f | oracle (Deep fixes L, everything else L) %.4f | images Deep fixes %.1f%%, Deep breaks %.1f%%" % (a1.mean(), a2.mean(), (a1 | a2).mean(), 100 * (~a1 & a2).mean(), 100 * (a1 & ~a2).mean()))
o = np.argsort(-S1, 1); top, snd = o[:, 0], o[:, 1]; st = S1[np.arange(n), top]; ss = S1[np.arange(n), snd]; marg = (st - ss).astype(np.float64)
CONF = np.isin(top, (0, 2, 3, 4, 6))
def acc_at(score, share):  # route the `share` of images with the LOWEST score
    k = int(round(share * n)); idx = np.argsort(score, kind="stable")[:k]; r = np.zeros(n, bool); r[idx] = True; return np.where(r, p2, p1).__eq__(y).mean()
feat = np.concatenate([np.eye(100)[top * 10 + snd], marg[:, None] / 1000.0, st[:, None] / 1000.0, ss[:, None] / 1000.0], 1)
def cross_fit(target):
    sc = np.zeros(n); f = np.random.RandomState(0).permutation(n); h = [f[: n // 2], f[n // 2:]]
    for a, b in ((0, 1), (1, 0)):
        m = LogisticRegression(max_iter=300, C=1.0).fit(feat[h[a]], target[h[a]]); sc[h[b]] = -m.predict_proba(feat[h[b]])[:, 1]   # low score = likely to need routing
    return sc
sig = {"margin (shipped)": marg, "margin, confusable top class only": np.where(CONF, marg, 1e9), "margin / top score": marg / (np.abs(st) + 1.0),
       "learned router: P(L wrong)": cross_fit(~a1), "learned router: P(Deep fixes L)": cross_fit(~a1 & a2), "ORACLE: Deep fixes L (not realisable)": -((~a1 & a2).astype(np.float64)) - 0.001 * (~a1)}
shares = (0.10, 0.15, 0.20, 0.30, 0.40)
print("%-42s" % "accuracy at routed share" + "".join("%9d%%" % round(100 * s) for s in shares))
for k, v in sig.items(): print("%-42s" % k + "".join("%10.4f" % acc_at(v, s) for s in shares), flush=True)
# ---- combining instead of replacing: a routed image takes argmax(S1 * wa + S2 * wb) (integer weights, adds and shifts only), routed by the shipped margin
print("\ncombining L and Deep scores on routed images (margin routing); weights wa:wb on S1:S2")
print("%-26s" % "wa:wb" + "".join("%9d%%" % round(100 * s) for s in shares))
for wa, wb in ((0, 1), (1, 1), (1, 2), (1, 4), (2, 1)):
    comb = (wa * S1 + wb * S2).argmax(1); row = []
    for s in shares:
        k = int(round(s * n)); idx = np.argsort(marg, kind="stable")[:k]; r = np.zeros(n, bool); r[idx] = True; row.append((np.where(r, comb, p1) == y).mean())
    print("%-26s" % ("%d:%d%s" % (wa, wb, " (shipped)" if (wa, wb) == (0, 1) else "")) + "".join("%10.4f" % v for v in row), flush=True)
