"""Bit-exact check of ldeep_core.v against the integer golden model (ldeep_golden.py). Run from anywhere: python hw/rtl/deep/run_check_deep.py. Never run two RTL checks in the same folder at once (they share out_deep.txt). 28 Oct 2026."""
import os, subprocess, sys
d = os.path.dirname(os.path.abspath(__file__)); os.chdir(d)
n = int([l.split()[1] for l in open("deep_params.txt") if l.startswith("NTEST")][0])
subprocess.check_call(["iverilog", "-g2012", "-o", "ldeep_sim", "-P", "ldeep_tb.NTEST=%d" % n, "ldeep_tb.v", "ldeep_core.v"]); subprocess.check_call(["vvp", "ldeep_sim"], stdout=subprocess.DEVNULL)
exp = [list(map(int, l.split())) for l in open("deep_exp.txt") if l.strip()]; got = [list(map(int, l.split())) for l in open("out_deep.txt") if l.strip()]
bad = [i for i, (e, g) in enumerate(zip(exp, got)) if e != g[:11]]; cyc = [g[11] for g in got]
print("images %d, expected %d, mismatches %d, mean cycles per routed image %.0f (min %d, max %d)" % (len(got), len(exp), len(bad), sum(cyc) / len(cyc), min(cyc), max(cyc)))
if bad: print("first mismatches:", bad[:5]); sys.exit(1)
print("PASS")
