#!/usr/bin/env python3
"""cortex_encoder.v built with ENC_LEARN vs hw/brain/detector_learn.py (bit-exact): learn from L images with a reseed
after RS of them and one at the end, then compare every counter of all 128 detectors and the codes of N test images
encoded with the learned detectors. usage: python run_check_encoder_learn.py DATA_DIR [mnist|fashion] [L] [RS] [N]"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
from feature_layer import Features, patches, binarize  # noqa
from detector_learn import StreamDetectors  # noqa
from cortex_core import load  # noqa
D = sys.argv[1]; DS = sys.argv[2] if len(sys.argv) > 2 else "mnist"
L, RS, N = (int(sys.argv[i]) if len(sys.argv) > i else d for i, d in ((3, 60), (4, 30), (5, 10)))
xtr, ytr, xte, yte = load(D, DS)
limgs = xtr[np.isin(ytr, (0, 1))][:L]
imgs = xte[np.random.RandomState(0).choice(len(xte), N, replace=False)]
fes = []
for c in (50, 150, ("on", 8), ("off", 8)):
    sd = StreamDetectors(); pp, _ = patches(binarize(limgs, c))
    sd.learn(pp[:RS]); r1 = sd.reseed(); sd.learn(pp[RS:]); r2 = sd.reseed()
    fe = Features(32, thr=c); fe.cnt = sd.cnt.copy(); fe.reseeded = r1 + r2; fes.append(fe)
exp = np.concatenate([f.encode(imgs) for f in fes], 1)
open(os.path.join(HERE, "img_learn.hex"), "w").write("\n".join("%02x" % v for v in limgs.reshape(-1)) + "\n")
open(os.path.join(HERE, "img.hex"), "w").write("\n".join("%02x" % v for v in imgs.reshape(-1)) + "\n")
subprocess.run(["iverilog", "-g2005", "-DENC_LEARN", "-o", "/tmp/encl.vvp", f"-Ptb_cortex_encoder_learn.L={L}",
                f"-Ptb_cortex_encoder_learn.RS={RS}", f"-Ptb_cortex_encoder_learn.N={N}",
                "cortex_encoder.v", "tb_cortex_encoder_learn.v"], cwd=HERE, check=True)
res = subprocess.run(["vvp", "-n", "/tmp/encl.vvp"], cwd=HERE, capture_output=True, text=True)
print(res.stdout.strip().splitlines()[0] if res.stdout.strip() else res.stderr[-400:])
words = [int(w, 16) for w in open(os.path.join(HERE, "out_lc.txt")).read().split()]
bad_c = 0
for ch in range(4):
    for d in range(32):
        w = words[ch * 32 + d]
        got = [((w >> (6 * q)) & 63) - (64 if (w >> (6 * q)) & 32 else 0) for q in range(25)]
        if got != fes[ch].cnt[d].tolist():
            bad_c += 1
            if bad_c <= 3: print("COUNTER MISMATCH channel", ch, "detector", d, got[:8], fes[ch].cnt[d][:8].tolist())
got = [list(map(int, line.split())) for line in open(os.path.join(HERE, "out_enc.txt")).read().split("\n")[:N]]
bad = sum(got[i] != np.nonzero(exp[i])[0].tolist() for i in range(N))
for p in ("img_learn.hex", "out_lc.txt"):
    os.remove(os.path.join(HERE, p))
print("detectors reseeded per channel:", [f.reseeded for f in fes])
print(f"{DS}: learned from {L} images (reseed after {RS} and at the end), counters compared 128 x 25, mismatching "
      f"detectors {bad_c}; {N} test images encoded with the learned detectors, mismatching images {bad}")
print("PASS" if bad == 0 and bad_c == 0 else "FAIL")
