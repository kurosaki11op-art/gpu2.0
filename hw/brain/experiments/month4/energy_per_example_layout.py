"""Energy per learned example and per decision from the SKY130 layout estimate (pipelined core, clock-gated, lighter
clock tree): count the chip's operations in the full 5-stage run (exact integer model, the month-2 rule) and multiply by
the cycles each operation takes in the RTL (measured in simulation) and the layout's energy per cycle (0.70-0.98 nJ at
50 MHz). ESTIMATED. usage: DATA_DIR mnist|fashion"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import CortexInt
from cortex_core import load
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr = z["tr"]
_, ytr, _, _ = load(D, DS); ytr = ytr.astype(np.int64)
CYC = {"predict": 264, "learn": 2465, "dream": 7109}          # pipelined core, RTL simulation (cycles per command)
NJ = (0.70, 0.98)                                           # layout energy per cycle, 1% / 10% activity
m = CortexInt(ctr.shape[1], night_stop=2, daydream=1); real = day_dreams = 0
for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
    sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(i).permutation(len(sel))]
    old = int(m.known.sum()); m.stage(ctr[sel], ytr[sel])
    real += len(sel); day_dreams += len(sel) + m.ndream * old           # one daydream per example + interleaved old
night = int(m.stats[0])
cycles = real * CYC["learn"] + (day_dreams + night) * CYC["dream"]
res = {"dataset": DS, "label": "ESTIMATED (layout energy per cycle x RTL cycles x operation counts)",
       "real_examples": real, "day_dreams": day_dreams, "night_dreams": night,
       "cycles_per_learned_example": round(cycles / real),
       "uJ_per_learned_example": [round(cycles / real * e / 1000, 1) for e in NJ],
       "uJ_per_decision": [round(CYC["predict"] * e / 1000, 3) for e in NJ]}
print(res, flush=True)
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"energy_layout_{DS}.json"), "w"), indent=1)
