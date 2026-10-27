"""27 Oct 2026, SIMULATED. Ceiling check for part 3: how well can a strong specialist separate Shirt from T-shirt, Pullover and Coat on the SAME inputs? A one-hidden-layer network (a GPU-style baseline, for reference only, not our chip) trained on the 4 confusable classes only, on raw pixels and on L's code. Compared with L's own table on the same 4-way test."""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, xtr, xte, train_table, CL
from sklearn.neural_network import MLPClassifier
mk, mt = np.isin(ytr, CL), np.isin(yte, CL); lab = {c: i for i, c in enumerate(CL)}; yt = np.array([lab[c] for c in ytr[mk]]); ye = np.array([lab[c] for c in yte[mt]]); sh = lab[6]
W = train_table(ctr[mk], ytr[mk]); p = (cte[mt].astype(np.int32) @ W)[:, CL].argmax(1); print("L's table (trained on the 4 classes only): 4-way acc %.4f, Shirt recall %.3f" % ((p == ye).mean(), (p[ye == sh] == sh).mean()), flush=True)
for nm, A, B in (("raw pixels /255", xtr[mk] / 255.0, xte[mt] / 255.0), ("L code bits", ctr[mk].astype(np.float32), cte[mt].astype(np.float32))):
    m = MLPClassifier((256,), max_iter=25, random_state=0).fit(A, yt); p = m.predict(B); print("MLP on %-16s: 4-way acc %.4f, Shirt recall %.3f" % (nm, (p == ye).mean(), (p[ye == sh] == sh).mean()), flush=True)
