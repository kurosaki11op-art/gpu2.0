#!/usr/bin/env python3
"""The PC-side schedule (cortex_host.run_stage on the emulator) must leave the chip in exactly the state the integer
chip model reaches (CortexInt.stage), on tasks where nights end early (clothing, sound) as well as digits.
usage: python check_host_schedule.py DATA_DIR"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "brain"))
from cortex_host import Emu, SEED_LANES, run_stage  # noqa
from cortex_int import CortexInt  # noqa
from cortex_core import load  # noqa
D = sys.argv[1]; ok = True
for ds in ("mnist", "fashion"):
    z = np.load(os.path.join(D, f"sep_{ds}_F32_p2.npz")); ctr = z["tr"]; _, ytr, _, _ = load(D, ds); ytr = ytr.astype(int)
    dev = Emu(ctr.shape[1]); dev.seed(SEED_LANES); dev.clear(); known = set()
    ref = CortexInt(ctr.shape[1], B=10, night=2, daydream=1, night_stop=2, seed=1)
    nights = []
    for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
        sel = np.concatenate([np.where(ytr == c)[0][:300] for c in s]); sel = sel[np.random.RandomState(i).permutation(len(sel))]
        nights.append(run_stage(dev, ctr[sel], ytr[sel], known)); ref.stage(ctr[sel], ytr[sel])
    same = np.array_equal(ref.W, dev.W) and np.array_equal(ref.on, dev.on) and np.array_equal(ref.n, dev.n)
    print(f"{ds}: night dreams per stage {nights}; host schedule == chip model: {same}")
    ok &= same
print("PASS" if ok else "FAIL")
