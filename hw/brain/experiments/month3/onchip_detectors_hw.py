"""Accuracy of the hardware detector-learning rule (hw/brain/detector_learn.py) vs PC-learned detectors, exact 5-stage
integer chip model. Stream = the first day's images (classes 0, 1; first 12,000) once. usage: DATA_DIR mnist|fashion"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from detector_learn import learn_features
from cortex_int import CortexInt
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; res = {}; t0 = time.time()
for every in (0, 1000):
    fes = learn_features(xtr[np.isin(ytr, (0, 1))][:12000], reseed_every=every)
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 2000]) for f in fes], 1) for i in range(0, len(x), 2000)])
    ctr, cte = enc(xtr), enc(xte); m = CortexInt(ctr.shape[1]); accs = []
    for i, s in enumerate(stages):
        sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(i).permutation(len(sel))]
        m.stage(ctr[sel], ytr[sel]); seen = np.isin(yte, sum(stages[:i + 1], ()))
        accs.append(round(float((m.predict(cte[seen]) == yte[seen]).mean()), 4))
    res[f"reseed_every_{every or 'end'}"] = accs
    print(DS, "reseed every", every or "end", accs, "%.0fs" % (time.time() - t0), flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (integer chip model, hardware learning rule)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"onchip_detectors_hw_{DS}.json"), "w"), indent=1)
