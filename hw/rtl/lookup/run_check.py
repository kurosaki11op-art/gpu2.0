#!/usr/bin/env python3
"""RTL vs reference model: drive the same bytes through spark_lookup.v (iverilog) and lookup_ref.py and compare every output.
usage: python run_check.py [<book dir>]     (prose slices are skipped if no book dir is given)"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "system"))
from lookup_ref import LookupCore  # noqa
Z = np.load(os.path.join(HERE, "..", "..", "system", "out", "slice_cache.npz"))
sets = {"code": bytes(Z["test_text"][:20000])}
if len(sys.argv) > 1:
    raw = open(os.path.join(sys.argv[1], "carroll-alice.txt"), "rb").read(); s0 = int(len(raw) * 0.4); sets["prose"] = raw[s0:s0 + 20000]
ok = True
for name, data in sets.items():
    for tb in (11, 12):
        n = len(data)
        open(os.path.join(HERE, "in.hex"), "w").write("\n".join("%02x" % b for b in data) + "\n")
        subprocess.run(["iverilog", "-g2005", "-o", "/tmp/lk_chk.vvp", f"-Ptb_spark_lookup.TB={tb}", f"-Ptb_spark_lookup.N={n}",
                        "spark_lookup.v", "tb_spark_lookup.v"], cwd=HERE, check=True)
        out = subprocess.run(["vvp", "-n", "/tmp/lk_chk.vvp"], cwd=HERE, capture_output=True, text=True).stdout
        cyc = [l for l in out.splitlines() if l.startswith("DONE")][0]
        core = LookupCore(tb); bad = 0; hits = 0
        for i, line in enumerate(open(os.path.join(HERE, "out.txt"))):
            p, h, o, c = line.split(); exp = core.step(data[i])
            got = (int(p, 16), int(h), int(o), int(c)); hits += got[1]
            if got != exp:
                bad += 1
                if bad <= 3: print("MISMATCH", name, tb, i, got, exp)
        print(f"{name:5s} TB={tb}: {n} bytes, mismatches {bad}, table hit rate {hits / n:.3f}   [{cyc}]")
        ok &= bad == 0
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
