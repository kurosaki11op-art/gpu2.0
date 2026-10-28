import os, shutil, subprocess, sys, tempfile
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(here, "..", "brain", "experiments", "month5")); import ldeep_ref as R
idx = int(sys.argv[1]); z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/deep_test_all.npz"); x = z["X"][idx]
r, S, p = R.run(x[None, :]); print("reference: routed", r[0], "scores", S[0].tolist(), "pred", p[0])
S1 = x[:4608].astype(np.int64) @ R.W1; srt = np.sort(S1); print("stage-1 scores", S1.tolist(), "margin", srt[-1] - srt[-2], "threshold", R.ROUTE_T)
t = tempfile.mkdtemp(); deep = os.path.join(here, "..", "rtl", "deep")
for f in ("deep_wcode1.hex", "deep_wcode.hex", "deep_wcl.hex", "deep_hdr.hex", "deep_lits.hex", "l_system.v", "l_system_tb.v"): shutil.copy(os.path.join(deep, f), t)
open(os.path.join(t, "sys_in.hex"), "w").write("%01544x\n" % int("".join(str(int(b)) for b in x[::-1]), 2)); subprocess.check_call(["iverilog", "-g2012", "-o", "sim", "-P", "l_system_tb.NTEST=1", "l_system_tb.v", "l_system.v"], cwd=t); subprocess.check_call(["vvp", "sim"], cwd=t, stdout=subprocess.DEVNULL)
print("RTL:", open(os.path.join(t, "out_sys.txt")).read().strip()); shutil.rmtree(t)
