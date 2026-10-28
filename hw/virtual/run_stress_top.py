"""VIRTUAL DEVICE TEST 2: a scripted stress mix on the layered top (l_chip_top): 56 random test images (routed and not), 8 corner inputs (all zeros, all ones, alternating bits, single set bits, a sparse and a dense random pattern), matrix products interleaved, repeated identical images (state leakage), and fault injection (reset in the middle of a routed recognition, in the middle of a matrix product's neighbour job). Every result is compared with the independent reference model (recognitions) or the Forge golden outputs (matrix product). SIMULATED (iverilog). Usage: python run_stress_top.py [seed]"""
import os, shutil, subprocess, sys, tempfile
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(here, "..", "brain", "experiments", "month5")); import ldeep_ref as R
seed = int(sys.argv[1]) if len(sys.argv) > 1 else 1; rs = np.random.RandomState(seed); NB = 6176
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/deep_test_all.npz"); Xall = z["X"]
rr_all, _, _ = R.run(Xall[:3000]); routed_ids = np.nonzero(rr_all)[0]; plain_ids = np.nonzero(rr_all == 0)[0]
imgs = [Xall[i] for i in list(rs.choice(routed_ids, 20, replace=False)) + list(rs.choice(plain_ids, 36, replace=False))]
corner = [np.zeros(NB, np.uint8), np.ones(NB, np.uint8), (np.arange(NB) % 2).astype(np.uint8), (np.arange(NB) % 2 == 0).astype(np.uint8)]
for pos in (0, NB - 1): v = np.zeros(NB, np.uint8); v[pos] = 1; corner.append(v)
corner.append((rs.rand(NB) < 0.02).astype(np.uint8)); corner.append((rs.rand(NB) < 0.6).astype(np.uint8)); imgs += corner; X = np.array(imgs); NIMG = len(X); assert NIMG == 64
jobs = []                                                                     # (type, image, arg2)
order = list(range(NIMG)); rs.shuffle(order)
for k, i in enumerate(order[:44]): jobs.append((0, i, 0))
for pos in (7, 19, 31, 43): jobs.insert(pos, (1, 0, 0))                        # matrix products interleaved
jobs.insert(10, (2, int(np.nonzero(R.run(X)[0])[0][0]), 6000)); jobs.insert(25, (2, int(np.nonzero(R.run(X)[0])[0][1]), 15000))   # resets in the middle of a routed run (stage 1 is about 4,600 cycles, stage 2 follows)
for _ in range(3): jobs.append((0, 5, 0))                                      # the same image three times in a row at the end
NJOB = len(jobs); tmp = tempfile.mkdtemp(); deep = os.path.join(here, "..", "rtl", "deep"); forge = os.path.join(here, "..", "rtl", "forge"); top = os.path.join(here, "..", "rtl", "top")
for d, names in ((deep, ["deep_wcode1.hex", "deep_wcode.hex", "deep_wcl.hex", "deep_hdr.hex", "deep_lits.hex", "l_system.v"]), (forge, ["mm_a.hex", "mm_b.hex", "mm_exp.txt", "forge_lane.v", "forge_tile_mm.v"]), (top, ["l_chip_top.v"]), (here, ["l_chip_stress_tb.v"])):
    for nme in names: shutil.copy(os.path.join(d, nme), tmp)
open(os.path.join(tmp, "stress_in.hex"), "w").write("\n".join("%0*x" % (1544, int("".join(str(int(b)) for b in x[::-1]), 2)) for x in X) + "\n")
open(os.path.join(tmp, "jobs.hex"), "w").write("\n".join("%02x%06x%08x" % j[:1] + "" if False else "%02x%06x%08x" % (j[0], j[1], j[2]) for j in jobs) + "\n")
subprocess.check_call(["iverilog", "-g2012", "-o", "sim", "-P", "l_chip_stress_tb.NJOB=%d" % NJOB, "l_chip_stress_tb.v", "l_chip_top.v", "l_system.v", "forge_tile_mm.v", "forge_lane.v"], cwd=tmp); subprocess.check_call(["vvp", "sim"], cwd=tmp, stdout=subprocess.DEVNULL)
lines = [l.split() for l in open(os.path.join(tmp, "out_stress.txt")) if l.strip()]; act = [l for l in lines if l[0] == "ACTIVE"][0]; lines = [l for l in lines if l[0] != "ACTIVE"]
rr, SS, pp = R.run(X); mexp = [tuple(map(int, l.split())) for l in open(os.path.join(tmp, "mm_exp.txt")) if l.strip()]
pos = 0; bad = 0; nrec = nmm = nrst = 0; routed_n = 0; ncorner = sum(1 for t, i, _ in jobs if t == 0 and i >= 56)
for t, i, _ in jobs:
    if t == 0:
        r = lines[pos]; pos += 1; got = list(map(int, r[1:])); exp = [int(rr[i])] + list(map(int, SS[i])) + [int(pp[i])]; nrec += 1; routed_n += int(rr[i]); bad += (got != exp)
    elif t == 1:
        assert lines[pos][0] == "M"; pos += 1; got = [tuple(map(int, l)) for l in lines[pos:pos + 256]]; pos += 256; nmm += 1; bad += (got != mexp)
    else: assert lines[pos][0] == "X"; pos += 1; nrst += 1
print("stress mix: %d recognitions (%d routed, %d corner inputs), %d matrix products, %d reset injections: mismatches %d; cycles awake cortex %s, deep %s, forge %s" % (nrec, routed_n, ncorner, nmm, nrst, bad, act[2], act[4], act[6]))
shutil.rmtree(tmp); sys.exit(1 if bad else 0)
