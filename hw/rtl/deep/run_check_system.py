"""Bit-exact check of l_system.v (two stages and dispatcher) against the integer golden pipeline: routed flag, 10 scores and prediction for 200 test images (routed and not). 28 Oct 2026. Run from anywhere; do not run two RTL checks in this folder at once."""
import os, subprocess, sys
d = os.path.dirname(os.path.abspath(__file__)); os.chdir(d)
subprocess.check_call(["iverilog", "-g2012", "-o", "lsys_sim", "l_system_tb.v", "l_system.v"]); subprocess.check_call(["timeout", "1500", "vvp", "lsys_sim"], stdout=subprocess.DEVNULL); os.remove("lsys_sim")
exp = [list(map(int, l.split())) for l in open("sys_exp.txt") if l.strip()]; got = [list(map(int, l.split())) for l in open("out_sys.txt") if l.strip()]
bad = [i for i, (e, g) in enumerate(zip(exp, got)) if e != g[:12]]
r = [g[12] for g, e in zip(got, exp) if e[0] == 1]; n = [g[12] for g, e in zip(got, exp) if e[0] == 0]
print("images %d, expected %d, routed %d, mismatches %d; mean cycles: not routed %.0f, routed %.0f, overall %.0f" % (len(got), len(exp), len(r), len(bad), sum(n) / max(1, len(n)), sum(r) / max(1, len(r)), sum(g[12] for g in got) / len(got)))
if bad or len(got) != len(exp): print("first mismatches:", bad[:5]); sys.exit(1)
print("PASS")
