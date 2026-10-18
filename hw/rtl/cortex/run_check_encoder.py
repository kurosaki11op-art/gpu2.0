#!/usr/bin/env python3
"""cortex_encoder.v vs Features.encode (bit-exact): the active code bits of every image must be identical.
usage: python run_check_encoder.py DATA_DIR [mnist|fashion] [N] [--asic] [--s1]   (--asic: the clock-gated ASIC build; --s1: finer winner grid, option ENC_S1)"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
from feature_layer import Features  # noqa
from cortex_core import load  # noqa
ASIC = "--asic" in sys.argv; S1 = "--s1" in sys.argv; sys.argv = [a for a in sys.argv if a not in ("--asic", "--s1")]
import feature_layer  # noqa
if S1:
    feature_layer.PS, feature_layer.ST = 5, 1
D = sys.argv[1]; DS = sys.argv[2] if len(sys.argv) > 2 else "mnist"; N = int(sys.argv[3]) if len(sys.argv) > 3 else 40
xtr, ytr, xte, yte = load(D, DS)
fes = [Features(32, thr=c, pool=4 if S1 else 2).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
imgs = xte[np.random.RandomState(0).choice(len(xte), N, replace=False)]
exp = np.concatenate([f.encode(imgs) for f in fes], 1)
words = []
for f in fes:
    for t in (f.cnt >= 0):
        words.append(sum(1 << i for i in range(25) if t[i]))
open(os.path.join(HERE, "tmpl.hex"), "w").write("\n".join("%07x" % w for w in words) + "\n")
open(os.path.join(HERE, "img.hex"), "w").write("\n".join("%02x" % v for v in imgs.reshape(-1)) + "\n")
subprocess.run(["iverilog", "-g2005"] + (["-DCORTEX_ASIC"] if ASIC else []) + (["-DENC_S1"] if S1 else []) + ["-o", "/tmp/enc.vvp", f"-Ptb_cortex_encoder.N={N}", "cortex_encoder.v", "tb_cortex_encoder.v"] + (["cortex_cg.v"] if ASIC else []),
               cwd=HERE, check=True)
res = subprocess.run(["vvp", "-n", "/tmp/enc.vvp"], cwd=HERE, capture_output=True, text=True)
print(res.stdout.strip().splitlines()[0] if res.stdout.strip() else res.stderr[-400:])
got = [list(map(int, line.split())) for line in open(os.path.join(HERE, "out_enc.txt")).read().split("\n")[:N]]
bad = 0
for i in range(N):
    e = np.nonzero(exp[i])[0].tolist()
    if got[i] != e:
        bad += 1
        if bad <= 3:
            print("MISMATCH image", i, "rtl", len(got[i]), "bits, model", len(e), "first diff:",
                  sorted(set(got[i]) ^ set(e))[:6])
print(f"{DS}{' (ASIC build, gated clocks)' if ASIC else ''}{' (finer grid ENC_S1)' if S1 else ''}: {N} images, active bits per image {exp.sum(1).mean():.0f}, mismatching images {bad}")
print("PASS" if bad == 0 else "FAIL")
