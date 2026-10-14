"""Run the integer reference model through 5 learning stages. usage: python run_int.py DATA_DIR mnist|fashion|speech
Uses the cached sensory codes made by proof_suite_v3.py (sep_<ds>_F<F>_p2.npz). Writes ../results/cortex_int_<ds>.json"""
import json, os, sys, time
import numpy as np
from cortex_int import CortexInt
from cortex_core import load

D, DS = sys.argv[1], sys.argv[2]
NIGHT = int(os.environ.get("NIGHT", "2")); B = int(os.environ.get("SB", "10"))
F = 64 if DS == "speech" else 32
z = np.load(os.path.join(D, f"sep_{DS}_F{F}_p2.npz")); ctr, cte = z["tr"], z["te"]
if DS == "speech":
    import cochlea
    _, ytr, _, yte = cochlea.load_speech(os.path.join(D, "speech"), os.path.join(D, "speech_pics_res.npz"), cochlea.sound_picture_res)
else:
    _, ytr, _, yte = load(D, DS)
ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
t0 = time.time(); m = CortexInt(ctr.shape[1], B=B, night=NIGHT); hist = []
for i, s in enumerate(stages):
    sel = np.where(np.isin(ytr, s))[0]
    sel = sel[np.random.RandomState(i).permutation(len(sel))]                # arrival order of the day's examples
    w = m.stage(ctr[sel], ytr[sel])
    seen = np.isin(yte, sum(stages[:i + 1], ()))
    hist.append({"stage": i + 1, "acc": float((m.predict(cte[seen]) == yte[seen]).mean()), "table_writes": int(w)})
    print(DS, "night", NIGHT, "B", B, hist[-1], f"{time.time()-t0:.0f}s", flush=True)
out = {"dataset": DS, "label": "SIMULATED (integer reference model)", "night_passes": NIGHT, "count_bits": B,
       "stages": hist, "memory_KB": {k: v / 8192 for k, v in m.memory_bits(B).items()}}
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", f"cortex_int_{DS}_n{NIGHT}.json"), "w"), indent=1)
