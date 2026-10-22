#!/usr/bin/env python3
"""RTL demo with the shipped learning rules (22 Oct 2026, SIMULATED RTL): the stage and night sequencer drives the core with the slow consolidating table (margin 256), real digit codes (NB 4,608). Digits 0-3 are taught as four stages of NPER examples (each new digit with dreams of the earlier ones and a short night), then NTEST held-out test digits are recognised with PREDICT (slow table).
The integer model (CortexSlow.stage) gets the same stages and must give the same predictions (bit-exact); the accuracy is computed from the RTL's own answers. Dream counts are reduced (NDREAM) because RTL simulation is slow; the shipped value is 1,500. usage: python run_slow_demo.py DATA_DIR"""
import os, subprocess, sys
import numpy as np
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
from cortex_slow import CortexSlow
from cortex_core import load
D = sys.argv[1]; NPER = int(os.environ.get("NPER", 60)); NTEST = int(os.environ.get("NTEST", 400)); NDREAM = int(os.environ.get("NDREAM", 10)); NIGHT = 1; DD = 1; NSTOP = 2
z = np.load(os.path.join(D, "sep_mnist_F32_p2.npz")); ctr, cte = z["tr"], z["te"]; _, ytr, _, yte = load(D, "mnist"); ytr, yte = ytr.astype(int), yte.astype(int); NB = ctr.shape[1]
r = np.random.RandomState(11); m = CortexSlow(NB, B=10, ndream=NDREAM, night=NIGHT, daydream=DD, night_stop=NSTOP, ch=100, K=5, FR=3, rnd=1, small="copy", margin=256); seeds = m.rng.copy(); words = [4]
for c in range(4):
    idx = r.choice(np.where(ytr == c)[0], NPER, replace=False); m.stage(ctr[idx], ytr[idx])
    words += [NDREAM, NIGHT, DD, 0, NSTOP, NPER, 1 << c]
    for i in idx: a = np.nonzero(ctr[i])[0].tolist(); words += [c, len(a)] + a
tests = r.choice(np.where(yte < 4)[0], NTEST, replace=False); words += [NTEST]
for t in tests: a = np.nonzero(cte[t])[0].tolist(); words += [len(a)] + a
exp = []
for t in tests:
    a = np.nonzero(cte[t])[0]; s = np.array([m.S[c, a].astype(np.int64).sum() if m.known[c] else -(1 << 40) for c in range(10)]); exp.append(int(s.argmax()))
open("seq_in.hex", "w").write("\n".join("%08x" % w for w in words) + "\n"); open("lanes.hex", "w").write("\n".join("%08x" % s for s in seeds) + "\n")
print("model accuracy on the same test images: %.1f %%" % (100 * np.mean(np.array(exp) == yte[tests])), flush=True)
subprocess.run(["iverilog", "-g2005", "-DCORTEX_SLOW", "-s", "tb_seq_pred", "-o", "/tmp/slowdemo/d.vvp", "-Ptb_seq_pred.NB=%d" % NB, "-Ptb_seq_pred.AW=13", "-Ptb_seq_pred.MARGIN=256", f"-Ptb_seq_pred.NW={len(words) + 16}", "cortex_core.v", "cortex_seq.v", "tb_seq_pred.v"], check=True)
print("simulating the RTL (slow) ...", flush=True)
res = subprocess.run("vvp -n d.vvp | grep ^stages", shell=True, capture_output=True, text=True); print(res.stdout.strip())
got = [int(l.split()[1]) for l in open("out_cortex.txt").read().split("\n") if l.startswith("P")]
bad = sum(1 for a, b in zip(got, exp) if a != b) + abs(len(got) - len(exp)); right = sum(1 for g, t in zip(got, yte[tests]) if g == t)
print(f"predictions: RTL vs integer model mismatches {bad} of {len(exp)}")
print(f"the simulated chip (sequencer + core + slow table) recognised {right} of {len(got)} held-out test digits ({100 * right / max(1, len(got)):.1f} %) after learning digits 0-3 from {NPER} examples each")
print("PASS" if bad == 0 else "FAIL")
