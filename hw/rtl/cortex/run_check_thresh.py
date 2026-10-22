#!/usr/bin/env python3
"""cortex_thresh.v (streaming quantile tracker + cue-threshold generator) vs cross_modal.quantile_track / cue_thresholds (22 Oct 2026), bit-exact. Streams: gaussian-like margins, heavy tails, a step change, saturation at 0 and at the top, n = 1..15; refs: random, zero, tiny, near the top.
usage: python run_check_thresh.py"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
import cross_modal  # noqa
W = 21
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/thr.vvp", "cortex_thresh.v", "tb_thresh.v"], cwd=HERE, check=True)
r = np.random.RandomState(24); bad = 0
cases = [("normal", 3, np.clip(r.normal(4000, 1500, 3000), 0, None)), ("median", 8, np.clip(r.normal(4000, 1500, 3000), 0, None)), ("heavy tail", 5, r.pareto(1.5, 3000) * 800),
         ("step", 8, np.concatenate([r.normal(500, 100, 800), r.normal(60000, 9000, 1500)]).clip(0, None)), ("to zero", 1, np.concatenate([r.normal(900000, 5000, 20), np.zeros(1500)])), ("to top", 15, np.concatenate([np.zeros(10), np.full(1500, (1 << W) - 1)])), ("n=12", 12, r.randint(0, 20000, 2500))]
refs = [0, 1, 2, 3, 7, 100, 4332, 3832, 123456, 1 << 18, (1 << 20) + 17, (1 << W) - 1] + [int(v) for v in r.randint(0, 1 << W, 40)]
for name, n, xs in cases:
    xs = [int(min(max(v, 0), (1 << W) - 1)) for v in xs]; words = [n, len(xs)] + xs + [len(refs)] + refs
    open(os.path.join(HERE, "thresh_in.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
    subprocess.run(f"vvp -n /tmp/thr.vvp | grep ^done", shell=True, cwd=HERE, capture_output=True, text=True)
    out = open(os.path.join(HERE, "thresh_out.txt")).read().split("\n"); qs = [int(l.split()[1]) for l in out if l.startswith("Q")]; ts = [[int(v) for v in l.split()[1:]] for l in out if l.startswith("T")]
    eq = cross_modal.quantile_track(xs, n, 9, 7, 2, W); et = [cross_modal.cue_thresholds(v, W) for v in refs]
    dq = sum(1 for a, b in zip(qs, eq) if a != b) + abs(len(qs) - len(eq)); dt = sum(1 for a, b in zip(ts, et) if a != b) + abs(len(ts) - len(et)); bad += dq + dt
    print(f"{name:10s} n={n:2d}: {len(xs)} samples, final q {qs[-1] if qs else None}, tracker differing {dq}; {len(refs)} refs, threshold sets differing {dt}")
print("PASS" if bad == 0 else "FAIL")
