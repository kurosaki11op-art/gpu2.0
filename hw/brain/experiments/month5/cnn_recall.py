"""27 Oct 2026, SIMULATED. Per-class recall of the small float CNN (32 shared 3x3 filters, backprop, 20 epochs; the 91.28% reference of the foundations study), so the Shirt-recall target is a measured number."""
import os, sys, time
os.environ["ONLY"] = "none"; os.environ["F"] = "32"
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import foundations_raw as R
from shirt_new_methods_setup import ytr, yte
t0 = time.time(); rs = np.random.RandomState(0); m = R.Model("cnn", False, F=32)
for e in range(20):
    order = rs.permutation(len(R.Xtr))
    for i in range(0, len(order), R.BS): j = order[i:i + R.BS]; m.step(R.Xtr[j], ytr[j])
p = np.concatenate([m.forward(R.Xte[i:i + 1000])[0].argmax(1) for i in range(0, len(R.Xte), 1000)])
names = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat", "Sandal", "Shirt", "Sneaker", "Bag", "Boot"]
print("CNN accuracy %.4f [%.0fs]" % ((p == yte).mean(), time.time() - t0))
for c in range(10): print("RESULT recall %-9s %.3f" % (names[c], (p[yte == c] == c).mean()))
mk = np.isin(yte, [0, 2, 4, 6]); print("RESULT cluster accuracy (4 classes, 10-way prediction restricted): %.4f" % ((p[mk] == yte[mk]).mean()))
print("RESULT Shirt predicted as: %s" % {names[k]: int((p[yte == 6] == k).sum()) for k in range(10) if (p[yte == 6] == k).sum()})
