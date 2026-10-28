"""Bit-exact check of ldeep_core.v against the integer golden model (ldeep_golden.py). Run from anywhere: python hw/rtl/deep/run_check_deep.py. Never run two RTL checks in the same folder at once (they share out_deep.txt). 28 Oct 2026."""
import os, subprocess, sys
d = os.path.dirname(os.path.abspath(__file__)); os.chdir(d)
n = int([l.split()[1] for l in open("deep_params.txt") if l.startswith("NTEST")][0])
bram = "--bram" in sys.argv; par = "--parallel" in sys.argv; tb, top, tbn, outf = ("ldeep_p_tb.v", "ldeep_core_p.v", "ldeep_p_tb", "out_deep_p.txt") if par else ("ldeep_bram_tb.v", "ldeep_core_bram.v", "ldeep_bram_tb", "out_deep_bram.txt") if bram else ("ldeep_tb.v", "ldeep_core.v", "ldeep_tb", "out_deep.txt")
subprocess.check_call(["iverilog", "-g2012", "-o", "ldeep_sim", "-P", "%s.NTEST=%d" % (tbn, n), tb, top]); subprocess.check_call(["timeout", "900", "vvp", "ldeep_sim"], stdout=subprocess.DEVNULL)
exp = [list(map(int, l.split())) for l in open("deep_exp.txt") if l.strip()]; got = [list(map(int, l.split())) for l in open(outf) if l.strip()]
bad = [i for i, (e, g) in enumerate(zip(exp, got)) if e != g[:11]]; cyc = [g[11] for g in got]
print("images %d, expected %d, mismatches %d, mean cycles per routed image %.0f (min %d, max %d)" % (len(got), len(exp), len(bad), sum(cyc) / len(cyc), min(cyc), max(cyc)))
if bad: print("first mismatches:", bad[:5]); sys.exit(1)
print("PASS")
