#!/usr/bin/env python3
"""cortex_cue.v vs cross_modal.cue_combine (21 Oct 2026), bit-exact: reliability-weighted combination of two senses' class scores (shifts only). Random cases: 10 / 6 / 2 / 1 known classes, ties, extreme scores, thresholds from a typical margin (ascending, with repeats allowed).
usage: python run_check_cue.py"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
import cross_modal  # noqa
C, SW, N = 10, 20, 200
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/cue.vvp", f"-Ptb_cue.NCASE={N}", "cortex_cue.v", "tb_cue.v"], cwd=HERE, check=True)
r = np.random.RandomState(21); bad = 0
for nk, scale in ((10, 4000), (6, 300), (2, 40000), (1, 100), (10, 500000), (3, 6)):
    known = np.zeros(C, bool); known[r.choice(C, nk, replace=False)] = True
    sa = np.clip(r.randint(-scale, scale, (N, C)), -(1 << 19), (1 << 19) - 1); sb = np.clip(r.randint(-scale * 2, scale * 2, (N, C)), -(1 << 19), (1 << 19) - 1)
    sa[r.rand(N, C) < 0.15] = 0; sb[r.rand(N, C) < 0.15] = 0; sa[:5] = 7; sb[:5, :] = -3                                  # ties
    ref_a, ref_b = max(scale // 3, 2), max(scale // 2, 2); T = lambda ref: np.array([int(np.ceil(ref * 2 ** (k - 0.5))) for k in range(-3, 4)])
    TA, TB = T(ref_a), T(ref_b); TB[2] = TB[3]                                                                           # a repeated threshold
    words = [int(v) for v in TA] + [int(v) for v in TB]
    for q in range(N): words += [int(sum(1 << c for c in range(C) if known[c]))] + [int(v) & 0xFFFFF for v in sa[q]] + [int(v) & 0xFFFFF for v in sb[q]]
    open(os.path.join(HERE, "cue_in.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
    subprocess.run("vvp -n /tmp/cue.vvp | grep ^cases", shell=True, cwd=HERE, capture_output=True, text=True)
    got = np.array([[int(t) for t in l.split()] for l in open(os.path.join(HERE, "cue_out.txt")).read().split("\n") if l.strip()])
    p, ia, ib = cross_modal.cue_combine(sa, sb, known, TA, TB, SW); exp = np.stack([p, ia, ib], 1)
    d = int((got != exp).any(1).sum()); bad += d; print(f"known {nk:2d}, score scale {scale:6d}: cases {N}, differing {d}; indices seen A {sorted(set(ia.tolist()))} B {sorted(set(ib.tolist()))}")
print("PASS" if bad == 0 else "FAIL")
