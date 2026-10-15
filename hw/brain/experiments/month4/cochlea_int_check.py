"""Sound with the integer (shift-add) cochlea vs the float cochlea: same detector learning, same 5-stage exact integer
chip model (month-2 rule). usage: DATA_DIR"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea, cochlea_int
from feature_layer import Features
from cortex_int import CortexInt
D = sys.argv[1]; t0 = time.time()
CH, F = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)), 64
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
res = {}
for name, fn, cache in (("float", cochlea.sound_picture_res, "speech_pics_res.npz"),
                        ("integer", lambda x: cochlea_int.sound_picture_int(x.astype(np.int16)), "speech_pics_int.npz")):
    xtr, ytr, xte, yte = cochlea.load_speech(os.path.join(D, "speech"), os.path.join(D, cache), fn)
    ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
    codes = os.path.join(D, "sep_speech_F64_p2.npz" if name == "float" else "sep_speech_int_F64_p2.npz")
    if os.path.exists(codes):
        z = np.load(codes); ctr, cte = z["tr"], z["te"]
    else:
        fes = [Features(F, thr=c).fit(xtr[np.isin(ytr, stages[0])][:12000]) for c in CH]
        enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
        ctr, cte = enc(xtr), enc(xte); np.savez_compressed(codes, tr=ctr, te=cte)
    m = CortexInt(ctr.shape[1], night_stop=2, daydream=1); accs = []
    for i, s in enumerate(stages):
        sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(i).permutation(len(sel))]
        m.stage(ctr[sel], ytr[sel]); seen = np.isin(yte, sum(stages[:i + 1], ()))
        accs.append(round(float((m.predict(cte[seen]) == yte[seen]).mean()), 4))
    res[name] = accs; print(name, accs, "%.0fs" % (time.time() - t0), flush=True)
json.dump({"label": "SIMULATED (exact integer chip model)", **res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cochlea_int_check.json"), "w"), indent=1)
