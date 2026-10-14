#!/usr/bin/env python3
"""spark_lookup2.v vs LookupCoreV2 (bit-exact): pred, hit, src, count, bucket and confidence on every byte.
usage: python run_check2.py [<book dir>]"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "system"))
from lookup_ref import LookupCoreV2  # noqa
lut = [int(x, 16) for x in open(os.path.join(HERE, "conf_lut.hex")).read().split()]
Z = np.load(os.path.join(HERE, "..", "..", "system", "out", "slice_cache.npz"))
sets = {"code": bytes(Z["test_text"][:20000])}
if len(sys.argv) > 1:
    raw = open(os.path.join(sys.argv[1], "carroll-alice.txt"), "rb").read(); s0 = int(len(raw) * 0.4); sets["prose"] = raw[s0:s0 + 20000]
ok = True
for name, data in sets.items():
    for tb in (10, 11):
        n = len(data)
        open(os.path.join(HERE, "in.hex"), "w").write("\n".join("%02x" % b for b in data) + "\n")
        subprocess.run(["iverilog", "-g2005", "-o", "/tmp/lk2.vvp", f"-Ptb_spark_lookup2.TB={tb}", f"-Ptb_spark_lookup2.N={n}",
                        "spark_lookup2.v", "tb_spark_lookup2.v"], cwd=HERE, check=True)
        subprocess.run(["vvp", "-n", "/tmp/lk2.vvp"], cwd=HERE, capture_output=True, text=True)
        core = LookupCoreV2(tb); bad = 0; acc = 0
        for i, line in enumerate(open(os.path.join(HERE, "out2.txt"))):
            p, h, s, c, bk, cf = line.split(); r = core.step(data[i])
            got = (int(p, 16), int(h), int(s), int(c), int(bk), int(cf)); exp = r + (lut[r[4]],)
            if i + 1 < n: acc += got[0] == data[i + 1]
            if got != exp:
                bad += 1
                if bad <= 3: print("MISMATCH", name, tb, i, got, exp)
        print(f"{name:5s} TB={tb}: {n} bytes, mismatches {bad}, accuracy {acc / (n - 1):.4f}")
        ok &= bad == 0
# configuration-port test: rewrite the confidence table at run time and check conf follows it
data = sets["code"][:3000]; n = len(data)
open(os.path.join(HERE, "in.hex"), "w").write("\n".join("%02x" % b for b in data) + "\n")
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/lk2.vvp", "-Ptb_spark_lookup2.TB=11", f"-Ptb_spark_lookup2.N={n}",
                "spark_lookup2.v", "tb_spark_lookup2.v"], cwd=HERE, check=True)
subprocess.run(["vvp", "-n", "/tmp/lk2.vvp", "+cfgtest"], cwd=HERE, capture_output=True, text=True)
core = LookupCoreV2(11); bad = 0
for i, line in enumerate(open(os.path.join(HERE, "out2.txt"))):
    f = line.split(); r = core.step(data[i])
    bad += (int(f[4]), int(f[5])) != (r[4], (7 * r[4] + 3) & 255)
print(f"config-port test: {n} bytes, mismatches {bad}"); ok &= bad == 0
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
