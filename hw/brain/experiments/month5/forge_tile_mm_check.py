"""28 Oct 2026, SIMULATED. Generates a matrix product for the L Forge tile RTL (hw/rtl/forge/forge_tile_mm.v), runs it in iverilog and compares every output (mantissa and exponent) with the lane golden model, then reports the error against fp64 and the cycle count (one block operation per cycle)."""
import os, subprocess, sys
import numpy as np
from forge_tile_model import bfp_encode
from forge_lane_golden import lane_dot
M, N, K = 16, 16, 128; NB = K // 16; rs = np.random.RandomState(5); A = rs.randn(M, K); B = rs.randn(K, N)
D = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "rtl", "forge"))
ma, ea = bfp_encode(A); mb, eb = bfp_encode(B.T)
word = lambda m, e: "%034x" % (((int(e) & 255) << 128) | sum((int(v) & 255) << (8 * k) for k, v in enumerate(m)))
open(os.path.join(D, "mm_a.hex"), "w").write("\n".join(word(ma[i, b], ea[i, b]) for i in range(M) for b in range(NB)) + "\n")
open(os.path.join(D, "mm_b.hex"), "w").write("\n".join(word(mb[j, b], eb[j, b]) for j in range(N) for b in range(NB)) + "\n")
subprocess.check_call(["iverilog", "-g2012", "-o", "mm_sim", "-P", "forge_tile_mm_tb.M=%d" % M, "-P", "forge_tile_mm_tb.N=%d" % N, "-P", "forge_tile_mm_tb.NB=%d" % NB, "forge_tile_mm_tb.v", "forge_tile_mm.v", "forge_lane.v"], cwd=D)
subprocess.check_call(["vvp", "mm_sim"], cwd=D, stdout=subprocess.DEVNULL); os.remove(os.path.join(D, "mm_sim"))
lines = open(os.path.join(D, "out_mm.txt")).read().split("\n"); cyc = int([l for l in lines if l.startswith("cycles")][0].split()[1]); got = [tuple(map(int, l.split())) for l in lines if l and not l.startswith("cycles")]
bad = 0; C = np.zeros((M, N))
for i in range(M):
    for j in range(N):
        m, e = 0, 0
        from forge_lane_golden import lane_step
        for b in range(NB): m, e = lane_step(m, e, b == 0, ma[i, b], mb[j, b], int(ea[i, b]), int(eb[j, b]))
        bad += (got[i * N + j] != (m, e)); C[i, j] = got[i * N + j][0] * 2.0 ** got[i * N + j][1]
open(os.path.join(D, "mm_exp.txt"), "w").write("\n".join("%d %d" % g for g in got) + "\n")
print("tile matrix product %dx%dx%d: %d of %d outputs differ from the lane golden model; error vs fp64 %.2e; %d cycles for %d block operations (%d multiply-accumulates)" % (M, K, N, bad, M * N, np.linalg.norm(C - A @ B) / np.linalg.norm(A @ B), cyc, M * N * NB, M * N * K))
sys.exit(1 if bad else 0)
