#!/usr/bin/env python3
"""cortex_look.v vs cross_modal.look_combine (21 Oct 2026), bit-exact: the second-look decision (A alone when sure, A + B when A's margin is below the threshold). Random cases: 10 / 6 / 2 / 1 known classes, ties, extreme scores, thresholds from 0 to above every margin.
usage: python run_check_look.py"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
import cross_modal  # noqa
C, SW, N = 10, 20, 200
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/look.vvp", f"-Ptb_look.NCASE={N}", "cortex_look.v", "tb_look.v"], cwd=HERE, check=True)
r = np.random.RandomState(22); bad = 0
for nk, scale, th in ((10, 4000, 800), (6, 300, 0), (2, 40000, 5000), (1, 100, 50), (10, 500000, 1 << 19), (3, 6, 3), (10, 4000, (1 << 21) - 1)):
    known = np.zeros(C, bool); known[r.choice(C, nk, replace=False)] = True
    sa = np.clip(r.randint(-scale, scale, (N, C)), -(1 << 19), (1 << 19) - 1); sb = np.clip(r.randint(-scale, scale, (N, C)), -(1 << 19), (1 << 19) - 1)
    sa[r.rand(N, C) < 0.15] = 0; sb[r.rand(N, C) < 0.15] = 0; sa[:5] = 7; sb[:5, :] = -3
    words = []
    for q in range(N): words += [th, int(sum(1 << c for c in range(C) if known[c]))] + [int(v) & 0xFFFFF for v in sa[q]] + [int(v) & 0xFFFFF for v in sb[q]]
    open(os.path.join(HERE, "look_in.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
    subprocess.run("vvp -n /tmp/look.vvp | grep ^cases", shell=True, cwd=HERE, capture_output=True, text=True)
    got = np.array([[int(t) for t in l.split()] for l in open(os.path.join(HERE, "look_out.txt")).read().split("\n") if l.strip()])
    p, lk = cross_modal.look_combine(sa, sb, known, th, SW); exp = np.stack([p, lk.astype(int)], 1)
    d = int((got != exp).any(1).sum()); bad += d; print(f"known {nk:2d}, scale {scale:6d}, threshold {th:8d}: cases {N}, second looks {int(lk.sum())}, differing {d}")
print("PASS" if bad == 0 else "FAIL")
