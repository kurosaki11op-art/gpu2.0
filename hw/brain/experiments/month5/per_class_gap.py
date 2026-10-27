"""27 Oct 2026, SIMULATED. Where is the accuracy gap to the CNN? Per-class recall of L shipped and of the best richer variant (7 channels, two-level output 1,2: 89.95), against the CNN's per-class recall (cnn_recall.log: 91.28 overall)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ytr, yte, ctr, cte, train_table
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"
names = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat", "Sandal", "Shirt", "Sneaker", "Bag", "Boot"]
cnn = [0.891, 0.978, 0.856, 0.936, 0.870, 0.984, 0.707, 0.958, 0.975, 0.973]
def recalls(A, B):
    W = train_table(A, ytr); p = (B.astype(np.int32) @ W).argmax(1); return np.array([(p[yte == c] == c).mean() for c in range(10)]), (p == yte).mean(), p
r0, a0, p0 = recalls(ctr, cte)
chs = ["t32", "t80", "t128", "t176", "t224", "on8", "off8"]; cn = {c: np.load(SP + "cnt_%s.npz" % c) for c in chs}
code = lambda w: np.concatenate([np.concatenate([(cn[c]["ab"[w]] >= t) for t in (1, 2)], 1) for c in chs], 1).astype(np.uint8)
r1, a1, p1 = recalls(code(0), code(1))
print("%-10s %8s %8s %8s %10s %10s" % ("class", "CNN", "L ship", "L rich", "CNN-ship", "CNN-rich"))
for c in range(10): print("%-10s %8.3f %8.3f %8.3f %+10.3f %+10.3f" % (names[c], cnn[c], r0[c], r1[c], cnn[c] - r0[c], cnn[c] - r1[c]))
print("%-10s %8.4f %8.4f %8.4f" % ("accuracy", 0.9128, a0, a1))
print("share of the CNN gap (to rich L) carried by the four upper-body classes (T-shirt, Pullover, Coat, Shirt): %.2f of %.4f" % (sum(cnn[c] - r1[c] for c in (0, 2, 4, 6)) / sum(cnn[c] - r1[c] for c in range(10)), sum(cnn[c] - r1[c] for c in range(10)) / 10))
conf = np.zeros((10, 10), int)
for t, p in zip(yte, p1): conf[t, p] += 1
print("largest confusions of rich L (true -> predicted, count): %s" % sorted([(int(conf[t, p]), names[t], names[p]) for t in range(10) for p in range(10) if t != p], reverse=True)[:8])
