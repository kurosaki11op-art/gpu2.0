#!/usr/bin/env python3
"""L Cortex + L Deep through the EXISTING Cortex blocks (cortex_encoder ENC_S1 + cortex_core CORTEX_SLOW with the new SLOAD) and the Deep stage 2 (l_system S1=0), vs the integer pipeline of ldeep_golden.py (sys_exp.txt):
for the first N test images (raw pixels in), compares routed flag, the ten final scores and the prediction.
usage: python run_check_full.py DATA_DIR [N]   (DATA_DIR holds the fashion files; run ldeep_golden.py first so the hex files and sys_exp.txt exist)"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); CX = os.path.join(HERE, "..", "cortex")
sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features  # noqa
from cortex_core import load  # noqa
D = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 20
xtr, ytr, xte, yte = load(D, "fashion"); ytr = ytr.astype(np.int64)
fes = [Features(32, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
words = [sum(1 << i for i in range(25) if t[i]) for f in fes for t in (f.cnt >= 0)]
open(os.path.join(HERE, "tmpl.hex"), "w").write("\n".join("%07x" % w for w in words) + "\n")
open(os.path.join(HERE, "full_img.hex"), "w").write("\n".join("%02x" % v for v in xte[:N].reshape(-1)) + "\n")
srcs = ["l_cortex_deep_tb.v", "l_cortex_deep.v", "l_system.v", "ldeep_core_p.v", os.path.join(CX, "cortex_core.v"), os.path.join(CX, "cortex_encoder.v")]
subprocess.run(["iverilog", "-g2005", "-DCORTEX_SLOW", "-DCORTEX_HOOKS", "-DENC_S1", "-o", "/tmp/full.vvp", f"-Pl_cortex_deep_tb.N={N}"] + srcs, cwd=HERE, check=True)
res = subprocess.run(["vvp", "-n", "/tmp/full.vvp"], cwd=HERE, capture_output=True, text=True); print(res.stdout.strip().splitlines()[-1] if res.stdout.strip() else res.stderr[-500:])
exp = [list(map(int, l.split())) for l in open(os.path.join(HERE, "sys_exp.txt")).read().strip().split("\n")][:N]
got = [list(map(int, l.split())) for l in open(os.path.join(HERE, "out_full.txt")).read().strip().split("\n")]
bad = 0; ov = 0
for i in range(N):
    e = exp[i]; g = got[i]; ov += g[-1]
    if g[:12] != e:
        bad += 1
        if bad <= 3: print("MISMATCH image", i, "rtl", g[:12], "model", e)
cyc = np.array([g[12] for g in got]); r = np.array([g[0] for g in got])
print("images %d, routed %d, mismatches %d, overlap errors %d; mean cycles %.0f (not routed %.0f, routed %.0f); encoder %.0f, core %.0f, deep (routed) %.0f" % (N, r.sum(), bad, ov, cyc.mean(), cyc[r == 0].mean() if (r == 0).any() else 0, cyc[r == 1].mean() if r.any() else 0, np.mean([g[13] for g in got]), np.mean([g[14] for g in got]), np.mean([g[15] for g in got if g[0]] or [0])))
print("PASS" if bad == 0 and ov == 0 else "FAIL")
