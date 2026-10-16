"""Redesign 5, step 1: rectangular receptive fields for the sound layer (hw/brain/sound_features.py). Words, aligned pictures (lead 6),
10 channels, detectors fitted on words 0-1 (as shipped) unless FITALL=1 (all training words, unlabelled). All at once and 5 stages,
3 seeds, exact integer chip model. usage: DATA_DIR  ph,pw,sy,sx,py,px,F [...]   e.g. 5,5,2,2,2,2,64 (today's)"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from sound_features import SoundFeatures
from cortex_int import CortexInt
from sound_align_confirm import align
D = sys.argv[1]
z = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = z["S"], z["y"], z["te"]
ytr, yte = y[~te].astype(np.int64), y[te].astype(np.int64)
P = align(S, 6); xtr, xte = P[~te], P[te]
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sound_rf.json"); res = json.load(open(out)) if os.path.exists(out) else {}
for spec in sys.argv[2:]:
    ph, pw, sy, sx, py, px, F = [int(v) for v in spec.split(",")]
    fitx = xtr if os.environ.get("FITALL") else xtr[np.isin(ytr, (0, 1))]
    fes = [SoundFeatures(F, c, ph, pw, sy, sx, py, px).fit(fitx[:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 3000]) for f in fes], 1) for i in range(0, len(x), 3000)])
    ctr, cte = enc(xtr), enc(xte); r = {"code_bits": int(ctr.shape[1]), "on_bits": float(ctr.sum(1).mean())}
    for sname, stages in (("all_at_once", [tuple(range(10))]), ("5_stages", [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)])):
        accs = []
        for seed in (1, 2, 3):
            m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
            for i, s in enumerate(stages):
                sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]
                m.stage(ctr[sel], ytr[sel])
            accs.append(float((m.predict(cte) == yte).mean()))
        r[sname] = round(float(np.mean(accs)), 4)
    key = spec + ("|fitall" if os.environ.get("FITALL") else ""); res[key] = r; print(key, r, flush=True)
    json.dump({"label": "SIMULATED (exact integer chip model, 3 seeds, aligned words)", **res}, open(out, "w"), indent=1)
