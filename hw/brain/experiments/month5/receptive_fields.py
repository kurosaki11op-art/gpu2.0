"""Larger receptive fields (24 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed). Failure studied: Shirt vs T-shirt/Pullover/Coat differ in parts (sleeves, collar, front opening) 6 to 10 pixels across, while the shipped detectors look at 5x5 patches.
Same learner (unsupervised Hebbian detectors, XNOR/popcount matching, k=1 winner), patch size PS and step ST varied; counting table (slow-table model). usage: CFGS="9,2,32,2 13,2,32,2" python receptive_fields.py DATA_DIR fashion"""
import sys, os, time, numpy as np
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import feature_layer
from feature_layer import Features
from cortex_core import load
from cortex_slow import CortexSlow
D, DS = sys.argv[1], sys.argv[2]; xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
CH = (50, 150, ("on", 8), ("off", 8)); cfgs = [tuple(int(v) for v in c.split(",")) for c in os.environ.get("CFGS", "9,2,32,2 13,2,32,2 9,1,32,4").split()]
for PS, ST, F, pool in cfgs:
    feature_layer.PS, feature_layer.ST = PS, ST; t0 = time.time()
    fes = [Features(F, thr=c, pool=pool).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 200]) for g in fes], 1) for i in range(0, len(x), 200)])
    ctr, cte = enc(xtr), enc(xte); m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel])
    S = m.S.astype(np.int32); p = (cte.astype(np.int32) @ S.T).argmax(1)
    print("patch %2d step %d F=%3d pool %d | code bits %6d | active/image %5.0f | accuracy %.4f | Shirt %.3f T-shirt %.3f Pullover %.3f Coat %.3f | %.0fs" % (PS, ST, F, pool, ctr.shape[1], cte.sum(1).mean(), (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[yte == 0] == 0).mean(), (p[yte == 2] == 2).mean(), (p[yte == 4] == 4).mean(), time.time() - t0), flush=True)
    np.savez_compressed("rf_%d_%d_%d_%d.npz" % (PS, ST, F, pool), scores=(cte.astype(np.int32) @ S.T))
