"""VIRTUAL DEVICE TEST 1: the whole 10,000-image test set through the L system RTL (l_system.v: stage 1, dispatcher, L Deep) in simulation, compared image by image with the independent reference model (ldeep_ref.py, written from the RTL memory files): routed flag, all 10 scores and the prediction must be identical. Reports accuracy from the RTL's own predictions, routed share, cycles per image and throughput at the virtual device clock. SIMULATED (iverilog). Usage: python run_full_testset.py [images] [processes]"""
import json, os, shutil, subprocess, sys, tempfile, time
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); deep = os.path.join(here, "..", "rtl", "deep"); sys.path.insert(0, os.path.join(here, "..", "brain", "experiments", "month5"))
import ldeep_ref as R
N = int(sys.argv[1]) if len(sys.argv) > 1 else 10000; P = int(sys.argv[2]) if len(sys.argv) > 2 else 4; CLK_HZ = json.load(open(os.path.join(here, "vfpga_device.json")))["clock_hz"]
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/deep_test_all.npz"); X, y = z["X"][:N], z["y"][:N]; t0 = time.time()
rr, SS, pp = R.run(X); print("reference model done [%.0fs]: accuracy %.4f, routed %.1f%%" % (time.time() - t0, (pp == y).mean(), 100 * rr.mean()), flush=True)
chunks = np.array_split(np.arange(N), P); procs = []; tmps = []
for c, idx in enumerate(chunks):
    t = tempfile.mkdtemp(prefix="vf%d_" % c); tmps.append(t)
    for f in ("deep_wcode1.hex", "deep_wcode.hex", "deep_wcl.hex", "deep_hdr.hex", "deep_lits.hex", "l_system.v", "l_system_tb.v"): shutil.copy(os.path.join(deep, f), t)
    open(os.path.join(t, "sys_in.hex"), "w").write("\n".join("%0*x" % (1544, int("".join(str(int(b)) for b in X[i][::-1]), 2)) for i in idx) + "\n")
    subprocess.check_call(["iverilog", "-g2012", "-o", "sim", "-P", "l_system_tb.NTEST=%d" % len(idx), "l_system_tb.v", "l_system.v"], cwd=t); procs.append(subprocess.Popen(["vvp", "sim"], cwd=t, stdout=subprocess.DEVNULL))
for p in procs: p.wait()
got = []
for t in tmps: got += [list(map(int, l.split())) for l in open(os.path.join(t, "out_sys.txt")) if l.strip()]; shutil.rmtree(t)
got = np.array(got); assert len(got) == N, (len(got), N)
exp = np.concatenate([rr[:, None], SS, pp[:, None]], 1); bad = np.nonzero((got[:, :12] != exp).any(1))[0]; cyc = got[:, 12]; acc = (got[:, 11] == y).mean()
res = {"images": N, "mismatches": int(len(bad)), "accuracy_rtl": float(acc), "routed_share": float(got[:, 0].mean()), "cycles_mean": float(cyc.mean()), "cycles_not_routed_mean": float(cyc[got[:, 0] == 0].mean()), "cycles_routed_mean": float(cyc[got[:, 0] == 1].mean()), "cycles_max": int(cyc.max()), "clock_hz": CLK_HZ,
       "images_per_s_at_clock": float(CLK_HZ / cyc.mean()), "ms_per_image_mean": float(1000 * cyc.mean() / CLK_HZ), "ms_per_image_routed_mean": float(1000 * cyc[got[:, 0] == 1].mean() / CLK_HZ), "wall_s": time.time() - t0}
json.dump(res, open(os.path.join(here, "results", "full_testset.json"), "w"), indent=1); print(json.dumps(res, indent=1))
if len(bad): print("first mismatching images:", bad[:10].tolist()); sys.exit(1)
print("PASS: all %d images identical to the reference model" % N)
