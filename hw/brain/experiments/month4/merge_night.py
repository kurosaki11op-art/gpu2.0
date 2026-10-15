"""Merge night variants (how strictly the night after a merge stops). Based on merge_seeds.py: chip A learns 0-4, chip B learns 5-9 (each one stage, month-2 rule); their
memories are added (table clipped to +-15, counters and counts added, halved if full) into a third chip, which then
sleeps one self-regulated night. Same procedure as hw/brain/month2_final.py; seeds change example orders and random
lanes. Exact integer chip model. Variants: STOPS env, e.g. "2,8,0" (0 = full night, no self-stop). usage: DATA_DIR mnist|fashion|speech"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt, _dream, _practise
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_floor_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y, te = f["y"], f["te"]; ytr, yte = y[~te], y[te]
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS)
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); NB = ctr.shape[1]
RULE = dict(B=10, night=2, daydream=1, night_stop=2); res = {}
STOPS = [int(v) for v in os.environ.get('STOPS', '2,8,0').split(',')]
for s in (1, 2, 3):
    order = lambda sel, k: sel[np.random.RandomState(1000 * s + k).permutation(len(sel))]
    A = CortexInt(NB, seed=10 * s + 1, **RULE); sa = order(np.where(ytr < 5)[0], 11); A.stage(ctr[sa], ytr[sa])
    B = CortexInt(NB, seed=10 * s + 2, **RULE); sb = order(np.where(ytr >= 5)[0], 12); B.stage(ctr[sb], ytr[sb])
    M = CortexInt(NB, seed=10 * s + 3, **RULE)
    M.W[:] = np.clip(A.W.astype(np.int16) + B.W, -15, 15); M.on[:] = A.on + B.on; M.n[:] = A.n + B.n; M.known[:] = True
    for c in range(10):
        while M.n[c] >= M.top:
            M.on[c] >>= 1; M.n[c] >>= 1
    added = float((M.predict(cte) == yte).mean())
    W0, on0, n0, r0 = M.W.copy(), M.on.copy(), M.n.copy(), M.rng.copy()
    for st in STOPS:
        M.W[:] = W0; M.on[:] = on0; M.n[:] = n0; M.rng[:] = r0
        buf = np.zeros(NB, np.int32); blockw = run = 0
        for p in range(2):
            stop = False
            for j in range(M.ndream * 10):
                c = j % 10; k = _dream(M.on, M.n, c, M.rng, buf); blockw += _practise(M.W, buf, k, c, M.known, M.margin, M.cmax); run += 1
                if st > 0 and run % 256 == 0:
                    if blockw > st:
                        stop = True; break
                    blockw = 0
            if stop:
                break
        r = {"added": round(added, 4), "after_night": round(float((M.predict(cte) == yte).mean()), 4), "dreams": run}
        res.setdefault(st, []).append(r); print(DS, "seed", s, "stop", st, r, flush=True)
means = {st: round(float(np.mean([r["after_night"] for r in v])), 4) for st, v in res.items()}
print(DS, "merge night variants, means", means, flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model, 3 seeds)", "runs": {str(k): v for k, v in res.items()},
           "means": {str(k): v for k, v in means.items()}},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"merge_night_{DS}.json"), "w"), indent=1)
