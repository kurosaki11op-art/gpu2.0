"""Features step 1 (clothing / digits): other sensory-layer settings with the slow table as readout (exact integer model, all at once, single view, 2 seeds).
spec = F:PS:ST:pool  (detectors per channel, receptive field side, stride, pool). Channels as shipped: thresholds 50, 150, centre-surround on / off. Detectors fitted on classes 0-1
(as shipped). usage: DATA_DIR DS spec [...]. SIMULATED."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import feature_layer
from feature_layer import Features
from cortex_core import load
from cortex_slow import CortexSlow
D, DS = sys.argv[1], sys.argv[2]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
CH = (50, 150, ("on", 8), ("off", 8)); res = {}
for spec in sys.argv[3:]:
    F, PS, ST, PL = [int(v) for v in spec.split(":")]
    feature_layer.PS, feature_layer.ST = PS, ST
    fes = [Features(F, thr=c, pool=PL).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)])
    ctr, cte = enc(xtr), enc(xte); accs = []
    for seed in (1, 2):
        m = CortexSlow(ctr.shape[1], ch=500, K=3, night_stop=2, daydream=1, seed=seed)
        sel = np.random.RandomState(100 * seed).permutation(len(ytr)); m.stage(ctr[sel], ytr[sel]); accs.append(float((m.predict(cte) == yte).mean()))
    res[spec] = {"code_bits": int(ctr.shape[1]), "acc": round(float(np.mean(accs)), 4)}; print(DS, spec, res[spec], flush=True)
    json.dump({"label": "SIMULATED (exact integer model + slow table, 2 seeds, all at once, single view), spec = F:PS:ST:pool", **res}, open(f"features_sweep2_{DS}.json", "w"), indent=1)
