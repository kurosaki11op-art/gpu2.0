"""Detector-layer grid: does a softer (k winners per spot) and larger (more detectors) learned feature layer lift the counting readout? (24 Oct 2026, SIMULATED, one seed)
Motivated by the literature: hard winner-take-all sparse Hebbian coding scales poorly; booleanisation / feature richness limits Tsetlin-style models more than the learner.
Single view, all at once, slow-table integer model, stride-1 5x5 patches, 4 channels (thresholds 50, 150, on/off cells), pool 4. usage: python feat_grid.py DATA_DIR fashion"""
import sys, os, time, numpy as np
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features
from cortex_core import load
from cortex_slow import CortexSlow
D, DS = sys.argv[1], sys.argv[2]; xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
CH = (50, 150, ("on", 8), ("off", 8)); cfgs = [tuple(int(v) for v in c.split(",")) for c in os.environ.get("CFGS", "32,1,4 32,3,4 64,1,4 64,3,4 128,1,4").split()]
for F, k, pool in cfgs:
    t0 = time.time(); fes = [Features(F, thr=c, pool=pool, k=k).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 200]) for g in fes], 1) for i in range(0, len(x), 200)])
    ctr, cte = enc(xtr), enc(xte)
    m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel])
    S = m.S.astype(np.int32); p = (cte.astype(np.int32) @ S.T).argmax(1)
    print("F=%3d k=%d pool=%d | code bits %6d | active bits/image %.0f | accuracy %.4f | Shirt recall %.3f | T-shirt %.3f | %.0fs" % (F, k, pool, ctr.shape[1], cte.sum(1).mean(), (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[yte == 0] == 0).mean(), time.time() - t0), flush=True)
