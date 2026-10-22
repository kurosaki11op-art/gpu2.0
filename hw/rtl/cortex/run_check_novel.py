#!/usr/bin/env python3
"""cortex_novel (in cortex_thresh.v) vs cross_modal.novelty_threshold (22 Oct 2026), bit-exact: the novelty threshold learned from the top scores of known pairs and the flags of test scores, including negative scores, scores equal to the threshold, extreme values, n = 1..15.
usage: python run_check_novel.py"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
import cross_modal  # noqa
SW = 20; LO, HI = -(1 << (SW - 1)), (1 << (SW - 1)) - 1
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/nov.vvp", "cortex_thresh.v", "tb_novel.v"], cwd=HERE, check=True)
r = np.random.RandomState(25); bad = 0
for name, n, cal in (("positive", 2, r.normal(9000, 2500, 2500)), ("mixed signs", 2, r.normal(0, 3000, 2500)), ("negative", 1, r.normal(-8000, 1500, 2000)), ("n=8", 8, r.normal(500, 4000, 2000)), ("extreme", 15, np.concatenate([np.full(300, HI), np.full(300, LO), r.randint(LO, HI, 800)]))):
    cal = [int(min(max(v, LO), HI)) for v in cal]; thr = cross_modal.novelty_threshold(cal, n, SW)
    test = [int(min(max(v, LO), HI)) for v in r.normal(np.mean(cal), 4000, 300)] + [thr, thr - 1, thr + 1, LO, HI, 0, -1, 1]
    words = [n, len(cal)] + [v & 0xFFFFF for v in cal] + [len(test)] + [v & 0xFFFFF for v in test]
    open(os.path.join(HERE, "novel_in.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
    subprocess.run("vvp -n /tmp/nov.vvp | grep ^done", shell=True, cwd=HERE, capture_output=True, text=True)
    out = open(os.path.join(HERE, "novel_out.txt")).read().split("\n"); got_t = int(out[0].split()[1]); got_f = [int(l.split()[2]) for l in out[1:] if l.startswith("F")]
    exp_f = [int(v < thr) for v in test]; d = int(got_t != thr) + sum(1 for a, b in zip(got_f, exp_f) if a != b) + abs(len(got_f) - len(exp_f)); bad += d
    print(f"{name:12s} n={n:2d}: threshold chip {got_t} model {thr}, {len(test)} flags, differing {d}, flagged {sum(exp_f)}")
print("PASS" if bad == 0 else "FAIL")
