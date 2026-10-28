"""VIRTUAL DEVICE TEST 5: the three stand-alone L Deep cores (asynchronous reads, block RAM, four parallel engines) on EVERY routed image of the 10,000-image test set (about 2,000 images), scores and prediction compared with the independent reference model's stage-2 result. The system run of Test 1 already covered the one-engine system core; this closes the gap left by the 300-image checks. SIMULATED (iverilog). Usage: python run_cores_testset.py [processes]"""
import json, os, shutil, subprocess, sys, tempfile, time
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); deep = os.path.join(here, "..", "rtl", "deep"); sys.path.insert(0, os.path.join(here, "..", "brain", "experiments", "month5")); import ldeep_ref as R
P = int(sys.argv[1]) if len(sys.argv) > 1 else 4; z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/deep_test_all.npz"); X, y = z["X"], z["y"]
rr, SS, pp = R.run(X); ids = np.nonzero(rr)[0]; Xr = X[ids]; print("routed images: %d" % len(ids), flush=True)
CORES = {"asynchronous-read core": ("ldeep_core.v", "ldeep_tb.v", "ldeep_tb", "out_deep.txt"), "block-RAM core": ("ldeep_core_bram.v", "ldeep_bram_tb.v", "ldeep_bram_tb", "out_deep_bram.txt"), "four-engine core": ("ldeep_core_p.v", "ldeep_p_tb.v", "ldeep_p_tb", "out_deep_p.txt")}
files = [f for f in os.listdir(deep) if f.endswith(".hex") and f != "deep_in.hex" and f != "sys_in.hex"]; ok_all = True; res = {}
for name, (src, tb, tbn, outf) in CORES.items():
    t0 = time.time(); chunks = np.array_split(np.arange(len(ids)), P); procs = []; tmps = []
    for c, idx in enumerate(chunks):
        t = tempfile.mkdtemp(prefix="core%d_" % c); tmps.append(t)
        for f in files + [src, tb]: shutil.copy(os.path.join(deep, f), t)
        open(os.path.join(t, "deep_in.hex"), "w").write("\n".join("%0*x" % (1544, int("".join(str(int(b)) for b in Xr[i][::-1]), 2)) for i in idx) + "\n")
        subprocess.check_call(["iverilog", "-g2012", "-o", "sim", "-P", "%s.NTEST=%d" % (tbn, len(idx)), tb, src], cwd=t); procs.append(subprocess.Popen(["vvp", "sim"], cwd=t, stdout=subprocess.DEVNULL))
    for p in procs: p.wait()
    got = []
    for t in tmps: got += [list(map(int, l.split())) for l in open(os.path.join(t, outf)) if l.strip()]; shutil.rmtree(t)
    got = np.array(got); exp = np.concatenate([SS[ids], pp[ids, None]], 1); bad = np.nonzero((got[:, :11] != exp).any(1))[0]; cyc = got[:, 11]
    res[name] = {"routed_images": len(ids), "mismatches": int(len(bad)), "cycles_mean": float(cyc.mean()), "cycles_max": int(cyc.max()), "seconds": round(time.time() - t0)}; ok_all &= (len(bad) == 0 and len(got) == len(ids))
    print("%-24s %d images, mismatches %d, mean cycles %.0f (max %d) [%.0fs]%s" % (name, len(got), len(bad), cyc.mean(), cyc.max(), time.time() - t0, "" if not len(bad) else "  first bad: %s" % bad[:5].tolist()), flush=True)
json.dump(res, open(os.path.join(here, "results", "cores_testset.json"), "w"), indent=1); print("PASS: all three cores identical to the reference on every routed image" if ok_all else "FAIL"); sys.exit(0 if ok_all else 1)
