"""VIRTUAL DEVICE TEST 3: L Forge stress. (a) the arithmetic lane on 200,000 random operations (random mantissas including extremes, exponent gaps from 0 to above the 40-bit alignment limit, runs of 1 to 16 blocks) against the integer golden model; (b) the matrix-product tile on seven data distributions (normal, heavy-tailed, 90% zeros, a wide dynamic range, all zeros, all maximum mantissas, alternating-sign extremes), every output against the lane golden model, and the error against fp64. SIMULATED (iverilog). Usage: python run_stress_forge.py"""
import os, random, shutil, subprocess, sys, tempfile
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); forge = os.path.join(here, "..", "rtl", "forge"); sys.path.insert(0, os.path.join(here, "..", "brain", "experiments", "month5"))
from forge_lane_golden import lane_step
from forge_tile_model import bfp_encode
# (a) lane, 200,000 operations
tmp = tempfile.mkdtemp(); [shutil.copy(os.path.join(forge, f), tmp) for f in ("forge_lane.v", "forge_lane_tb.v")]; rnd = random.Random(7); lines = []; m, e = 0, 0; hx = lambda v: "".join("%02x" % (x & 255) for x in v[::-1]); n_ops = 0
while n_ops < 200000:
    n = rnd.randint(1, 16); base = rnd.randint(-60, 60); mode = rnd.random()
    for b in range(n):
        kind = rnd.random(); ma = [rnd.choice([127, -127, 0, 1, -1]) if kind < 0.15 else rnd.randint(-127, 127) for _ in range(16)]; mb = [rnd.choice([127, -127, 0, 1, -1]) if kind > 0.85 else rnd.randint(-127, 127) for _ in range(16)]
        ea = max(-127, min(127, base + (rnd.randint(-80, 80) if mode < 0.3 else rnd.randint(-4, 4)))); eb = rnd.randint(-10, 10); first = 1 if b == 0 else 0; m, e = lane_step(m, e, first, ma, mb, ea, eb)
        lines.append("%d %d %d %s %s %d %d" % (first, ea, eb, hx(ma), hx(mb), m, e)); n_ops += 1
open(os.path.join(tmp, "lane_vec.txt"), "w").write("\n".join(lines) + "\n"); subprocess.check_call(["iverilog", "-g2012", "-o", "sim", "forge_lane_tb.v", "forge_lane.v"], cwd=tmp); out = subprocess.check_output(["vvp", "sim"], cwd=tmp).decode(); print("lane: " + [l for l in out.split("\n") if l.startswith("LANE")][0]); shutil.rmtree(tmp)
# (b) tile matrix product on several distributions
M, N, K = 16, 16, 128; NB = K // 16; rs = np.random.RandomState(3); fails = 0
def dist(name):
    if name == "normal": return rs.randn(M, K), rs.randn(K, N)
    if name == "heavy-tailed": return rs.standard_t(2, (M, K)), rs.standard_t(2, (K, N))
    if name == "90% zeros": return rs.randn(M, K) * (rs.rand(M, K) < 0.1), rs.randn(K, N) * (rs.rand(K, N) < 0.1)
    if name == "wide dynamic range": return rs.randn(M, K) * 10.0 ** rs.uniform(-4, 4, (M, K)), rs.randn(K, N) * 10.0 ** rs.uniform(-4, 4, (K, N))
    if name == "all zeros": return np.zeros((M, K)), np.zeros((K, N))
    if name == "all maximum": return np.ones((M, K)), np.ones((K, N))
    return np.where((np.arange(K)[None, :] % 2) == 0, 1.0, -1.0) * np.ones((M, 1)), np.where((np.arange(K)[:, None] % 2) == 0, 1.0, -1.0) * np.ones((1, N))
word = lambda mm, ee: "%034x" % (((int(ee) & 255) << 128) | sum((int(v) & 255) << (8 * k) for k, v in enumerate(mm)))
print("%-20s %12s %12s %10s" % ("data", "mismatches", "error vs fp64", "cycles"))
for name in ("normal", "heavy-tailed", "90% zeros", "wide dynamic range", "all zeros", "all maximum", "alternating extremes"):
    A, B = dist(name); ma, ea = bfp_encode(A); mb, eb = bfp_encode(B.T); tmp = tempfile.mkdtemp(); [shutil.copy(os.path.join(forge, f), tmp) for f in ("forge_lane.v", "forge_tile_mm.v", "forge_tile_mm_tb.v")]
    open(os.path.join(tmp, "mm_a.hex"), "w").write("\n".join(word(ma[i, b], ea[i, b]) for i in range(M) for b in range(NB)) + "\n"); open(os.path.join(tmp, "mm_b.hex"), "w").write("\n".join(word(mb[j, b], eb[j, b]) for j in range(N) for b in range(NB)) + "\n")
    subprocess.check_call(["iverilog", "-g2012", "-o", "sim", "-P", "forge_tile_mm_tb.M=%d" % M, "-P", "forge_tile_mm_tb.N=%d" % N, "-P", "forge_tile_mm_tb.NB=%d" % NB, "forge_tile_mm_tb.v", "forge_tile_mm.v", "forge_lane.v"], cwd=tmp); subprocess.check_call(["vvp", "sim"], cwd=tmp, stdout=subprocess.DEVNULL)
    ls = open(os.path.join(tmp, "out_mm.txt")).read().split("\n"); cyc = int([l for l in ls if l.startswith("cycles")][0].split()[1]); got = [tuple(map(int, l.split())) for l in ls if l and not l.startswith("cycles")]; bad = 0; C = np.zeros((M, N))
    for i in range(M):
        for j in range(N):
            mm_, ee_ = 0, 0
            for b in range(NB): mm_, ee_ = lane_step(mm_, ee_, b == 0, ma[i, b], mb[j, b], int(ea[i, b]), int(eb[j, b]))
            bad += (got[i * N + j] != (mm_, ee_)); C[i, j] = got[i * N + j][0] * 2.0 ** got[i * N + j][1]
    ref = A @ B; err = np.linalg.norm(C - ref) / (np.linalg.norm(ref) + 1e-300) if np.linalg.norm(ref) > 0 else float(np.abs(C).max()); fails += bad; print("%-20s %12d %12.2e %10d" % (name, bad, err, cyc), flush=True); shutil.rmtree(tmp)
print("tile mismatches in total: %d" % fails); sys.exit(1 if fails else 0)
