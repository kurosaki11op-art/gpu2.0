#!/usr/bin/env python3
"""The whole 10,000-image test set through the integrated chip RTL (cortex_encoder + cortex_core inference build + dispatcher + four-engine L Deep: l_cortex_deep.v), raw pixels in,
sharded over P processes, compared image by image with the independent reference model (ldeep_ref.py, which works from the cached codes, so the RTL encoder is checked too).
usage: python run_full_chip.py DATA_DIR [N] [P]   -> hw/virtual/results/full_chip.json"""
import glob, json, os, shutil, subprocess, sys, tempfile, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); CX = os.path.join(HERE, "..", "cortex")
sys.path.insert(0, os.path.join(HERE, "..", "..", "brain")); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain", "experiments", "month5"))
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features  # noqa
from cortex_core import load  # noqa
import ldeep_ref as R
D = sys.argv[1]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 10000; P = int(sys.argv[3]) if len(sys.argv) > 3 else 4; t0 = time.time()
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/deep_test_all.npz"); X, y = z["X"][:N], z["y"][:N]
rr, SS, pp = R.run(X); print("reference model done [%.0fs]: accuracy %.4f, routed %.1f%%" % (time.time() - t0, (pp == y).mean(), 100 * rr.mean()), flush=True)
xtr, ytr, xte, yte = load(D, "fashion"); ytr = ytr.astype(np.int64); assert (yte[:N] == y).all()
fes = [Features(32, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
tm = "\n".join("%07x" % sum(1 << i for i in range(25) if t[i]) for f in fes for t in (f.cnt >= 0)) + "\n"
srcs = ["l_cortex_deep_tb.v", "l_cortex_deep.v", "l_system.v", "ldeep_core_p.v", os.path.join(CX, "cortex_core.v"), os.path.join(CX, "cortex_encoder.v")]
chunks = np.array_split(np.arange(N), P); procs = []; tmps = []
for c, idx in enumerate(chunks):
    t = tempfile.mkdtemp(prefix="fc%d_" % c, dir="/tmp"); tmps.append(t)
    for f in glob.glob(os.path.join(HERE, "deep_*.hex")): shutil.copy(f, t)
    open(os.path.join(t, "tmpl.hex"), "w").write(tm); open(os.path.join(t, "full_img.hex"), "w").write("\n".join("%02x" % v for v in xte[idx].reshape(-1)) + "\n")
    subprocess.check_call(["iverilog", "-g2005", "-DCORTEX_SLOW", "-DCORTEX_HOOKS", "-DENC_S1", "-DENC_PAIR", "-DCORTEX_INFER", "-o", "sim", "-Pl_cortex_deep_tb.N=%d" % len(idx)] + [os.path.abspath(os.path.join(HERE, s)) if not os.path.isabs(s) else s for s in srcs], cwd=t)
    procs.append(subprocess.Popen(["vvp", "-n", "sim"], cwd=t, stdout=subprocess.DEVNULL))
for p in procs: p.wait()
got = []
for t in tmps: got += [list(map(int, l.split())) for l in open(os.path.join(t, "out_full.txt")) if l.strip()]; shutil.rmtree(t)
got = np.array(got); assert len(got) == N, (len(got), N)
exp = np.concatenate([rr[:, None], SS, pp[:, None]], 1); bad = np.nonzero((got[:, :12] != exp).any(1))[0]; cyc = got[:, 12]
res = {"images": N, "mismatches": int(len(bad)), "overlap_errors": int(got[:, -1].sum()), "accuracy_rtl": float((got[:, 11] == y).mean()), "routed_share": float(got[:, 0].mean()), "cycles_mean": float(cyc.mean()),
       "cycles_not_routed_mean": float(cyc[got[:, 0] == 0].mean()), "cycles_routed_mean": float(cyc[got[:, 0] == 1].mean()), "encoder_cycles_mean": float(got[:, 13].mean()), "core_cycles_mean": float(got[:, 14].mean()),
       "deep_cycles_routed_mean": float(got[got[:, 0] == 1, 15].mean()), "wall_s": time.time() - t0}
os.makedirs(os.path.join(HERE, "..", "..", "virtual", "results"), exist_ok=True); json.dump(res, open(os.path.join(HERE, "..", "..", "virtual", "results", "full_chip.json"), "w"), indent=1); print(json.dumps(res, indent=1))
if len(bad): print("first mismatching images:", bad[:10].tolist()); sys.exit(1)
print("PASS: all %d images identical to the reference model" % N)
