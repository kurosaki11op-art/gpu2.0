"""MESH TEST: generates a P x P mesh of L Forge tiles with routers (hw/rtl/mesh/mesh_tile.v), runs a distributed matrix product C = A B (SUMMA-style, K split over the mesh) in iverilog, compares EVERY output (mantissa and exponent) with the lane golden model, and reports cycles (communication, compute), link traversals and the lane utilisation, against the model's traffic assumption. SIMULATED. Usage: python gen_and_check.py [P] [MT] [NT] [NBT]   (defaults 4 4 4 2; C is (P*MT) x (P*NT), K = P*NBT*16)"""
import os, shutil, subprocess, sys, tempfile
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); forge = os.path.join(here, "..", "forge"); sys.path.insert(0, os.path.join(here, "..", "..", "brain", "experiments", "month5"))
from forge_tile_model import bfp_encode
from forge_lane_golden import lane_step
P = int(sys.argv[1]) if len(sys.argv) > 1 else 4; MT = int(sys.argv[2]) if len(sys.argv) > 2 else 4; NT = int(sys.argv[3]) if len(sys.argv) > 3 else 4; NBT = int(sys.argv[4]) if len(sys.argv) > 4 else 2
M, N, K = P * MT, P * NT, P * NBT * 16; KB = P * NBT; rs = np.random.RandomState(P * 100 + MT); A = rs.randn(M, K); B = rs.randn(K, N)
ma, ea = bfp_encode(A); mb, eb = bfp_encode(B.T)                   # A rows and B columns in blocks of 16 along K
word = lambda mm, ee: "%034x" % (((int(ee) & 255) << 128) | sum((int(v) & 255) << (8 * k) for k, v in enumerate(mm)))
tmp = tempfile.mkdtemp(); shutil.copy(os.path.join(here, "mesh_tile.v"), tmp); shutil.copy(os.path.join(forge, "forge_lane.v"), tmp)
for i in range(P):
    for j in range(P):
        open(os.path.join(tmp, "mesh_a_%d_%d.hex" % (i, j)), "w").write("\n".join(word(ma[i * MT + m, j * NBT + b], ea[i * MT + m, j * NBT + b]) for m in range(MT) for b in range(NBT)) + "\n")
        open(os.path.join(tmp, "mesh_b_%d_%d.hex" % (i, j)), "w").write("\n".join(word(mb[j * NT + n, i * NBT + b], eb[j * NT + n, i * NBT + b]) for n in range(NT) for b in range(NBT)) + "\n")
v = ["module mesh_top (input clk, input rst, input start, output reg done, output reg [31:0] cyc_comm, output reg [31:0] cyc_comp, output reg [31:0] hops_a, output reg [31:0] hops_b, input [15:0] rd_tile, input [15:0] rd_idx, output reg signed [16:0] rd_macc, output reg signed [11:0] rd_eacc);"]
v.append("    wire [%d:0] oe, ow, on, os; wire [%d:0] cd, pd, ta_all, tb_all; reg go_comm, go_comp;" % (161 * P * P - 1, P * P - 1))
v.append("    wire [%d:0] ta, tb; wire signed [%d:0] cmv; wire signed [%d:0] cev; reg [15:0] ra_;" % (32 * P * P - 1, 17 * P * P - 1, 12 * P * P - 1))
for i in range(P):
    for j in range(P):
        t = i * P + j; sl = lambda w, tt: "[%d:%d]" % (w * (tt + 1) - 1, w * tt)
        inw = "oe%s" % sl(161, i * P + j - 1) if j > 0 else "161'b0"; ine = "ow%s" % sl(161, i * P + j + 1) if j < P - 1 else "161'b0"; inn = "os%s" % sl(161, (i - 1) * P + j) if i > 0 else "161'b0"; ins = "on%s" % sl(161, (i + 1) * P + j) if i < P - 1 else "161'b0"
        v.append("    mesh_tile #(.I(%d), .J(%d), .P(%d), .MT(%d), .NT(%d), .NBT(%d), .FA(\"mesh_a_%d_%d.hex\"), .FB(\"mesh_b_%d_%d.hex\")) t%d (.clk(clk), .rst(rst), .go_comm(go_comm), .go_comp(go_comp), .in_w(%s), .in_e(%s), .in_n(%s), .in_s(%s), .out_e(oe%s), .out_w(ow%s), .out_n(on%s), .out_s(os%s), .comm_done(cd[%d]), .comp_done(pd[%d]), .tx_a(ta%s), .tx_b(tb%s), .c_raddr(rd_idx), .c_macc(cmv%s), .c_eacc(cev%s));" % (i, j, P, MT, NT, NBT, i, j, i, j, t, inw, ine, inn, ins, sl(161, t), sl(161, t), sl(161, t), sl(161, t), t, t, sl(32, t), sl(32, t), sl(17, t), sl(12, t)))
v.append("    integer q; reg [31:0] sa, sb; reg [2:0] st; always @(*) begin sa = 0; sb = 0; for (q = 0; q < %d; q = q + 1) begin sa = sa + ta[32*q +: 32]; sb = sb + tb[32*q +: 32]; end end" % (P * P))
v.append("    always @(posedge clk) begin if (rst) begin st <= 0; done <= 0; go_comm <= 0; go_comp <= 0; cyc_comm <= 0; cyc_comp <= 0; end else begin go_comm <= 0; go_comp <= 0; done <= 0; case (st) 0: if (start) begin go_comm <= 1; cyc_comm <= 0; cyc_comp <= 0; st <= 1; end 1: begin cyc_comm <= cyc_comm + 1; if (&cd) begin go_comp <= 1; hops_a <= sa; hops_b <= sb; st <= 2; end end 2: begin cyc_comp <= cyc_comp + 1; if (&pd) begin done <= 1; st <= 0; end end endcase end end")
v.append("    always @(posedge clk) begin rd_macc <= cmv[17*rd_tile +: 17]; rd_eacc <= cev[12*rd_tile +: 12]; end")
v.append("endmodule")
open(os.path.join(tmp, "mesh_top.v"), "w").write("\n".join(v) + "\n")
tb = """`timescale 1ns/1ps
module mesh_tb; reg clk = 0, rst = 1, start = 0; wire done; wire [31:0] cc, cp, ha, hb; reg [15:0] rt, ri; wire signed [16:0] rm; wire signed [11:0] re; integer f, t, k;
 mesh_top dut (.clk(clk), .rst(rst), .start(start), .done(done), .cyc_comm(cc), .cyc_comp(cp), .hops_a(ha), .hops_b(hb), .rd_tile(rt), .rd_idx(ri), .rd_macc(rm), .rd_eacc(re));
 always #5 clk = ~clk; initial begin repeat (3) @(posedge clk); rst = 0; @(negedge clk); start = 1; @(negedge clk); start = 0; wait (done); repeat (3) @(negedge clk); f = $fopen("out_mesh.txt", "w"); $fwrite(f, "cycles %0d %0d hops %0d %0d\\n", cc, cp, ha, hb);
  for (t = 0; t < NTILES; t = t + 1) for (k = 0; k < NELEM; k = k + 1) begin rt = t; ri = k; repeat (3) @(negedge clk); $fwrite(f, "%0d %0d\\n", rm, re); end $fclose(f); $finish; end endmodule
""".replace("NTILES", str(P * P)).replace("NELEM", str(MT * NT))
open(os.path.join(tmp, "mesh_tb.v"), "w").write(tb)
subprocess.check_call(["iverilog", "-g2012", "-o", "sim", "mesh_tb.v", "mesh_top.v", "mesh_tile.v", "forge_lane.v"], cwd=tmp); r = subprocess.run(["timeout", "600", "vvp", "sim"], cwd=tmp, capture_output=True, text=True)
lines = open(os.path.join(tmp, "out_mesh.txt")).read().split("\n"); hdr = lines[0].split(); cc, cp, ha, hb = int(hdr[1]), int(hdr[2]), int(hdr[4]), int(hdr[5]); got = [tuple(map(int, l.split())) for l in lines[1:] if l.strip()]
bad = 0; C = np.zeros((M, N))
for i in range(P):
    for j in range(P):
        for m in range(MT):
            for n in range(NT):
                mm_, ee_ = 0, 0
                for kb in range(KB): mm_, ee_ = lane_step(mm_, ee_, kb == 0, ma[i * MT + m, kb], mb[j * NT + n, kb], int(ea[i * MT + m, kb]), int(eb[j * NT + n, kb]))
                g = got[(i * P + j) * MT * NT + m * NT + n]; bad += (g != (mm_, ee_)); C[i * MT + m, j * NT + n] = g[0] * 2.0 ** g[1]
ref = A @ B; err = np.linalg.norm(C - ref) / np.linalg.norm(ref); T = P * P; block_ops = M * N * KB; single = block_ops + 3
recv_words = T * (P - 1) * (MT * NBT + NT * NBT)           # words that must arrive in the tiles (A from row mates, B from column mates)
print("mesh %dx%d (%d tiles), C %dx%d, K %d: mismatches %d of %d outputs, error vs fp64 %.2e" % (P, P, T, M, N, K, bad, M * N, err))
print("  cycles: communication %d + compute %d = %d; one tile alone %d -> speedup %.1fx of the ideal %dx (lane utilisation over the whole run %.0f%%)" % (cc, cp, cc + cp, single, single / (cc + cp), T, 100 * block_ops / ((cc + cp) * T)))
print("  link traversals: A %d, B %d, total %d; words delivered %d -> %.2f traversals per delivered word (the traffic model assumed 1.0 for pipelined broadcasts)" % (ha, hb, ha + hb, recv_words, (ha + hb) / recv_words))
shutil.rmtree(tmp); sys.exit(1 if bad else 0)
