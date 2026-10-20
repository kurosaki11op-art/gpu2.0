"""Clothing with no picture labels (20 Oct 2026) SIMULATED. The digits result (a heard word names pictures; sleep-time neighbour cleaning of the names) applied to clothing (Fashion-MNIST). There is no spoken clothing set, so the ear is SIMULATED as a labeller that is right a given share of the time:
  uniform   a wrong name is any other class (random)
  confusable a wrong name is one of the 2 classes whose mean code overlaps the true class most (shirt, T-shirt, pullover, coat ...: the errors a real listener or describer would make)
Names right: 73 % (27 % wrong) and 60 % (40 % wrong). One pass, chip rule margin 256 / 1,500 dreams / 1 night, 3 seeds; picture code = the shipped 4,608 bits. Compared: names as given, names cleaned in sleep (cross_modal.learn_picture: K = 8, buffer 256, ear vote, 2 rounds), true labels (reference).
usage: DATA_DIR"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import detector_learn, cross_modal
from cortex_core import load
D = sys.argv[1]; t0 = time.time(); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; SEEDS = 3
xtr, ytr, xte, yte = load(D, "fashion"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]; ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)]); vtr, vte = enc(xtr), enc(xte)
mean = np.stack([vtr[ytr == c].mean(0) for c in range(10)]); ovm = mean @ mean.T; np.fill_diagonal(ovm, -1); near = np.argsort(-ovm, 1)[:, :2]            # the 2 classes most alike in code space
acc = lambda m, c, y: float((m.predict(c) == y).mean()); R = {}
print("picture code", vtr.shape, "most alike classes", {c: near[c].tolist() for c in range(10)}, "| %.0fs" % (time.time() - t0), flush=True)
for seed in range(1, SEEDS + 1):
    r = np.random.RandomState(seed); R.setdefault("true labels (reference)", []).append(acc(cross_modal.fit(vtr, ytr, seed), vte, yte))
    for kind in ("uniform", "confusable"):
        for wrong in (0.27, 0.40):
            names = ytr.copy(); flip = r.rand(len(ytr)) < wrong
            if kind == "uniform": names[flip] = (ytr[flip] + r.randint(1, 10, flip.sum())) % 10
            else: names[flip] = near[ytr[flip], r.randint(0, 2, flip.sum())]
            tag = "%s, %d %% wrong" % (kind, int(wrong * 100)); R.setdefault(tag + " | as given", []).append(acc(cross_modal.fit(vtr, names, seed), vte, yte))
            m, lab = cross_modal.learn_picture(vtr, names, rounds=2, seed=seed); R.setdefault(tag + " | cleaned", []).append(acc(m, vte, yte)); R.setdefault(tag + " | cleaned names right", []).append(float((lab == ytr).mean()))
    print("seed", seed, "%.0fs" % (time.time() - t0), flush=True)
for k, v in R.items(): print("%-52s %.4f" % (k, np.mean(v)), flush=True)
