#!/usr/bin/env python3
"""cortex_encoder_gen.v vs Features.encode (bit-exact) for images (4 channels x 32 detectors) and sound pictures from
the chip's integer cochlea with its noise floor (10 channels x 64 detectors).
usage: python run_check_encoder_gen.py DATA_DIR image|sound [N]"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
from feature_layer import Features  # noqa
from cortex_core import load  # noqa
import cochlea_int  # noqa
D, MODE = sys.argv[1], sys.argv[2]; N = int(sys.argv[3]) if len(sys.argv) > 3 else 4
if MODE == "image":
    xtr, ytr, xte, _ = load(D, "mnist"); CH, F, LF = (50, 150, ("on", 8), ("off", 8)), 32, 5
else:
    z = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = z["S"], z["y"], z["te"]
    v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
    lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
    P = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8)
    xtr, ytr, xte = P[~te], y[~te], P[te]
    CH, F, LF = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)), 64, 6
fes = [Features(F, thr=c).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
imgs = xte[np.random.RandomState(0).choice(len(xte), N, replace=False)]
exp = np.concatenate([f.encode(imgs) for f in fes], 1)
words = [sum(1 << i for i in range(25) if t[i]) for f in fes for t in (f.cnt >= 0)]
open(os.path.join(HERE, "tmpl.hex"), "w").write("\n".join("%07x" % w for w in words) + "\n")
open(os.path.join(HERE, "img.hex"), "w").write("\n".join("%02x" % v for v in imgs.reshape(-1)) + "\n")
thr = "".join("%02x" % (c[1] if isinstance(c, tuple) else c) for c in reversed(CH))
kind = sum((0 if not isinstance(c, tuple) else 1 if c[0] == "on" else 2) << (2 * i) for i, c in enumerate(CH))
NCH = len(CH)
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/encg.vvp", f"-Ptb_cortex_encoder_gen.N={N}", f"-Ptb_cortex_encoder_gen.NCH={NCH}",
                f"-Ptb_cortex_encoder_gen.F={F}", f"-Ptb_cortex_encoder_gen.LF={LF}",
                f"-Ptb_cortex_encoder_gen.THR={8 * NCH}'h{thr}", f"-Ptb_cortex_encoder_gen.KIND={2 * NCH}'d{kind}",
                "cortex_encoder_gen.v", "tb_cortex_encoder_gen.v"], cwd=HERE, check=True)
res = subprocess.run(["vvp", "-n", "/tmp/encg.vvp"], cwd=HERE, capture_output=True, text=True)
print(res.stdout.strip().splitlines()[0] if res.stdout.strip() else res.stderr[-400:])
got = [list(map(int, l.split())) for l in open(os.path.join(HERE, "out_enc.txt")).read().split("\n")[:N]]
bad = 0
for i in range(N):
    e_ = np.nonzero(exp[i])[0].tolist()
    if got[i] != e_:
        bad += 1
        if bad <= 3:
            print("MISMATCH picture", i, "rtl", len(got[i]), "model", len(e_), "first diff", sorted(set(got[i]) ^ set(e_))[:6])
print(f"{MODE}: {N} pictures, code bits {exp.shape[1]}, active per picture {exp.sum(1).mean():.0f}, mismatching {bad}")
print("PASS" if bad == 0 else "FAIL")
