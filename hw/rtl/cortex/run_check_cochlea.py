#!/usr/bin/env python3
"""cortex_cochlea.v vs hw/brain/cochlea_int.py (bit-exact, with the noise floor): every pixel of the sound pictures of N
speech clips.
usage: python run_check_cochlea.py DATA_DIR [N]"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
import cochlea, cochlea_int  # noqa
D = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 4
root = os.path.join(D, "speech"); r = np.random.RandomState(0); clips = []
for k in range(N):
    w = cochlea.WORDS[k % len(cochlea.WORDS)]; fs = sorted(os.listdir(os.path.join(root, w)))
    clips.append(cochlea.read(os.path.join(root, w, fs[r.randint(len(fs))])))
X = np.stack(clips).astype(np.int16)
exp = cochlea_int.sound_picture_int(X)
open(os.path.join(HERE, "smp.hex"), "w").write("\n".join("%04x" % (int(v) & 0xFFFF) for v in X.reshape(-1)) + "\n")
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/coch.vvp", f"-Ptb_cortex_cochlea.N={N}", "cortex_cochlea.v",
                "tb_cortex_cochlea.v"], cwd=HERE, check=True)
res = subprocess.run(["vvp", "-n", "/tmp/coch.vvp"], cwd=HERE, capture_output=True, text=True)
print(res.stdout.strip().splitlines()[0] if res.stdout.strip() else res.stderr[-400:])
got = [list(map(int, l.split())) for l in open(os.path.join(HERE, "out_coch.txt")).read().split("\n")[:N]]
bad = 0
for i in range(N):
    if got[i] != exp[i].tolist():
        bad += 1
        if bad <= 3:
            d = [j for j in range(min(len(got[i]), 784)) if got[i][j] != exp[i][j]]
            print("MISMATCH clip", i, "pixels", len(got[i]), "differing", len(d), "first", d[:5],
                  [got[i][j] for j in d[:3]], [int(exp[i][j]) for j in d[:3]])
os.remove(os.path.join(HERE, "smp.hex"))
print(f"{N} clips, 784 pixels each, mismatching clips {bad}")
print("PASS" if bad == 0 else "FAIL")
