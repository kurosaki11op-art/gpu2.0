"""Modality dropout (20 Oct 2026) SIMULATED. Each class has a name heard when it is seen: a fixed sparse pattern of 1,024 bits (64 on) with 10 % of its bits flipped each time (a stand-in for the sound of the class's name; no audio exists for clothing). The chip learns pictures (4,608 bits) joined with the name code; the name code is missing from a share DROP of the learning examples (modality dropout, so the picture bits keep learning instead of leaning on the name); the same name-code share is dreamed. Tested with the PICTURE ALONE (name blank), 5 stages of 2 classes with the chip's dreams, margin 256 / 1,500 dreams / 1 night, 3 seeds.
Arms: picture alone (shipped), picture + name with DROP = 0 / 0.5 / 0.8. Clothing and digits; reports staged and one pass. usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, detector_learn
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; NN = 1024
for DS in ("fashion", "mnist"):
    xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:2000] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]; ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
    fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)]); ctr, cte = enc(xtr), enc(xte)
    g = np.random.RandomState(9); proto = np.zeros((10, NN), bool)
    for c in range(10): proto[c, g.choice(NN, 64, replace=False)] = True
    res = {}
    for drop in (None, 0.0, 0.5, 0.8):
        for staged in (False, True):
            acc = []
            for seed in (1, 2, 3):
                r = np.random.RandomState(seed + 31)
                if drop is None: code, tcode = ctr, cte
                else:
                    nm = proto[ytr] ^ (r.rand(len(ytr), NN) < 0.10); nm &= (r.rand(len(ytr), 1) >= drop); code = np.concatenate([ctr, nm], 1); tcode = np.concatenate([cte, np.zeros((len(cte), NN), bool)], 1)
                m = CortexSlow(code.shape[1], ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)
                for i, s in enumerate(STAGES if staged else [tuple(range(10))]):
                    o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(code[o], ytr[o])
                acc.append(float((m.predict(tcode) == yte).mean()))
            res[(drop, staged)] = np.mean(acc)
    for drop in (None, 0.0, 0.5, 0.8):
        print(DS, "picture alone (shipped)" if drop is None else "picture + name code, dropout %.1f, tested with the picture only" % drop, "| one pass %.4f | staged %.4f" % (res[(drop, False)], res[(drop, True)]), flush=True)
