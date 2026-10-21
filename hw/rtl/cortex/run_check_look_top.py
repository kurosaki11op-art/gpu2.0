#!/usr/bin/env python3
"""Two cores (a coarse and a fine table with different code widths, imported over the MEM interface) + cortex_look.v vs the model (21 Oct 2026), bit-exact: for random code lists the class score of each core, the look flag and the decision equal cross_modal.look_combine on the model's own scores (sums of the table fields over the active bits).
usage: python run_check_look_top.py"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
import cross_modal  # noqa
C, NA, NBW, N = 10, 640, 1024, 60
subprocess.run(["iverilog", "-g2005", "-DCORTEX_HOOKS", "-s", "tb_look_top", "-o", "/tmp/lt.vvp", f"-Ptb_look_top.NA={NA}", f"-Ptb_look_top.NBW={NBW}", f"-Ptb_look_top.NMAX={3 + NA + NBW + N * (2 * 400 + 2) + 100}", "cortex_core.v", "cortex_look.v", "tb_look_top.v"], cwd=HERE, check=True)
r = np.random.RandomState(23); bad = 0
for nk, th in ((10, 300), (7, 60), (10, 0), (10, 1 << 20)):
    known = np.zeros(C, bool); known[r.choice(C, nk, replace=False)] = True
    WA = r.randint(-15, 16, (C, NA)); WB = r.randint(-15, 16, (C, NBW)); WA[:, ::7] = 0
    la = [np.sort(r.choice(NA, r.randint(20, 200), replace=False)) for _ in range(N)]; lb = [np.sort(r.choice(NBW, r.randint(20, 300), replace=False)) for _ in range(N)]
    pack = lambda W, b: sum((int(W[c, b]) & 0x1F) << (5 * c) for c in range(C))
    words = [th, int(sum(1 << c for c in range(C) if known[c])), N] + [pack(WA, b) for b in range(NA)] + [pack(WB, b) for b in range(NBW)]
    for i in range(N): words += [len(la[i])] + [int(v) for v in la[i]] + [len(lb[i])] + [int(v) for v in lb[i]]
    open(os.path.join(HERE, "look_top_in.hex"), "w").write("\n".join("%016x" % w for w in words) + "\n")
    # the core's "known" classes: mark them (op 5) is not needed here: the second-look unit gets the mask from the testbench
    subprocess.run("vvp -n /tmp/lt.vvp | grep ^cases", shell=True, cwd=HERE, capture_output=True, text=True)
    got = np.array([[int(t) for t in l.split()] for l in open(os.path.join(HERE, "look_top_out.txt")).read().split("\n") if l.strip()])
    sa = np.stack([WA[:, l].sum(1) for l in la]); sb = np.stack([WB[:, l].sum(1) for l in lb]); p, lk = cross_modal.look_combine(sa, sb, known, th)
    exp = np.stack([p, lk.astype(int), sa[:, 0], sb[:, 0]], 1); d = int((got != exp).any(1).sum()); bad += d
    print(f"known {nk:2d}, threshold {th:8d}: cases {N}, second looks {int(lk.sum())}, differing {d}")
print("PASS" if bad == 0 else "FAIL")
