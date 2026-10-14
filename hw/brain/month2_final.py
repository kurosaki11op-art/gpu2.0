"""Month-2 final numbers on the exact integer chip model (cortex_int.py), one rule for every task:
5-bit fast table decides; 10-bit synaptic-scaling dream counters; one daydream per real example; a night of up to 2
passes that ends itself after a block of 256 dreams with more than 2 surprises. Every real example is seen once.
Tests: all at once (one stage with all 10 classes), 5 stages, merge (chip A 0-4 + chip B 5-9: add tables, add
counts, then one self-regulated night). usage: python month2_final.py DATA_DIR mnist|fashion|speech"""
import json, os, sys, time
import numpy as np
from cortex_int import CortexInt, _dream, _practise
from cortex_core import load

D, DS = sys.argv[1], sys.argv[2]
F = 64 if DS == "speech" else 32
z = np.load(os.path.join(D, f"sep_{DS}_F{F}_p2.npz")); ctr, cte = z["tr"], z["te"]
if DS == "speech":
    import cochlea
    _, ytr, _, yte = cochlea.load_speech(os.path.join(D, "speech"), os.path.join(D, "speech_pics_res.npz"), cochlea.sound_picture_res)
else:
    _, ytr, _, yte = load(D, DS)
ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
NB = ctr.shape[1]; RULE = dict(B=10, night=2, daydream=1, night_stop=2)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
t0 = time.time(); R = {"dataset": DS, "label": "SIMULATED (integer chip model, bit-exact with the RTL core)", "rule": RULE}


def order(sel, seed):
    return sel[np.random.RandomState(seed).permutation(len(sel))]


def acc(m, mask=None):
    mask = np.ones(len(yte), bool) if mask is None else mask
    return float((m.predict(cte[mask]) == yte[mask]).mean())


m = CortexInt(NB, **RULE); m.stage(ctr[order(np.arange(len(ytr)), 9)], ytr[order(np.arange(len(ytr)), 9)])
R["all_at_once"] = acc(m)
print(DS, "all at once", R["all_at_once"], f"{time.time()-t0:.0f}s", flush=True)
m = CortexInt(NB, **RULE); R["stages"] = []
for i, s in enumerate(stages):
    sel = order(np.where(np.isin(ytr, s))[0], i); m.stage(ctr[sel], ytr[sel])
    R["stages"].append(acc(m, np.isin(yte, sum(stages[:i + 1], ()))))
print(DS, "stages", np.round(R["stages"], 4), f"{time.time()-t0:.0f}s", flush=True)
A = CortexInt(NB, seed=1, **RULE); sa = order(np.where(ytr < 5)[0], 11); A.stage(ctr[sa], ytr[sa])
B = CortexInt(NB, seed=2, **RULE); sb = order(np.where(ytr >= 5)[0], 12); B.stage(ctr[sb], ytr[sb])
M = CortexInt(NB, seed=3, **RULE)
M.W[:] = np.clip(A.W.astype(np.int16) + B.W, -15, 15); M.on[:] = A.on + B.on; M.n[:] = A.n + B.n; M.known[:] = True
for c in range(10):                                                       # synaptic scaling if a merged count is full
    while M.n[c] >= M.top:
        M.on[c] >>= 1; M.n[c] >>= 1
added = acc(M)
buf = np.zeros(NB, np.int32); blockw = run = 0
for p in range(2):                                                        # one self-regulated night, all classes
    stop = False
    for j in range(M.ndream * 10):
        c = j % 10; k = _dream(M.on, M.n, c, M.rng, buf); blockw += _practise(M.W, buf, k, c, M.known, M.margin, M.cmax); run += 1
        if run % 256 == 0:
            if blockw > 2:
                stop = True; break
            blockw = 0
    if stop:
        break
R["merge"] = {"chip_A_0to4": acc(A), "chip_B_5to9": acc(B), "added_no_sleep": added, "after_night": acc(M), "night_dreams": run}
print(DS, "merge", R["merge"], f"{time.time()-t0:.0f}s", flush=True)
R["memory_KB"] = {"fast_table_5bit": 10 * NB * 5 / 8192, "dream_counts_10bit": (10 * NB + 10) * 10 / 8192}
json.dump(R, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", f"cortex_month2_final_{DS}.json"), "w"), indent=1)
