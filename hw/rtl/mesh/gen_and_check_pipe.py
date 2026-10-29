"""MESH OVERLAP TEST (29 Oct 2026, SIMULATED RTL). A stream of NP independent matrix products C_t = A_t B_t on a P x P mesh of double-buffered L Forge tiles (mesh_tile_pipe.v), run twice with the same hardware and data: SEQUENTIAL (communicate product t, then compute it, then the next)
and OVERLAPPED (while product t computes, the routers deliver the operands of product t+1 into the other operand bank). Every output (mantissa and exponent) of every product is compared with the lane golden model; cycles of the two runs are compared.
usage: python gen_and_check_pipe.py [P] [MT] [NT] [NBT] [NP]"""
import os, shutil, subprocess, sys, tempfile
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); forge = os.path.join(here, "..", "forge"); sys.path.insert(0, os.path.join(here, "..", "..", "brain", "experiments", "month5"))
from forge_tile_model import bfp_encode
from forge_lane_golden import lane_step
a = [int(x) for x in sys.argv[1:]]; P, MT, NT, NBT, NP = (a + [4, 4, 4, 2, 4][len(a):])[:5]
M, N, K = P * MT, P * NT, P * NBT * 16; KB = P * NBT; T = P * P
word = lambda mm, ee: "%034x" % (((int(ee) & 255) << 128) | sum((int(v) & 255) << (8 * k) for k, v in enumerate(mm)))
prods = []
for t in range(NP):
    rs = np.random.RandomState(1000 * t + P * 100 + MT); A = rs.randn(M, K); B = rs.randn(K, N); ma, ea = bfp_encode(A); mb, eb = bfp_encode(B.T); prods.append((A, B, ma, ea, mb, eb))
def build(tmp, ovl):
    shutil.copy(os.path.join(here, "mesh_tile_pipe.v"), tmp); shutil.copy(os.path.join(forge, "forge_lane.v"), tmp)
    for i in range(P):
        for j in range(P):
            open(os.path.join(tmp, "mesh_a_%d_%d.hex" % (i, j)), "w").write("\n".join(word(ma[i * MT + m, j * NBT + b], ea[i * MT + m, j * NBT + b]) for (_, _, ma, ea, _, _) in prods for m in range(MT) for b in range(NBT)) + "\n")
            open(os.path.join(tmp, "mesh_b_%d_%d.hex" % (i, j)), "w").write("\n".join(word(mb[j * NT + n, i * NBT + b], eb[j * NT + n, i * NBT + b]) for (_, _, _, _, mb, eb) in prods for n in range(NT) for b in range(NBT)) + "\n")
    sl = lambda w, tt: "[%d:%d]" % (w * (tt + 1) - 1, w * tt)
    v = ["module mesh_top (input clk, input rst, input start, output reg done, output reg [31:0] cyc, output reg [31:0] hops_a, output reg [31:0] hops_b, input [15:0] rd_tile, input [15:0] rd_idx, output reg signed [16:0] rd_macc, output reg signed [11:0] rd_eacc);"]
    v.append("    wire [%d:0] oe, ow, on, os; wire [%d:0] cd, pd; reg go_comm, go_comp, stop_comm; reg [7:0] comm_prod, comp_prod; reg comm_bank, comp_bank;" % (161 * T - 1, T - 1))
    v.append("    wire [%d:0] ta, tb; wire signed [%d:0] cmv; wire signed [%d:0] cev;" % (32 * T - 1, 17 * T - 1, 12 * T - 1))
    for i in range(P):
        for j in range(P):
            t = i * P + j
            inw = "oe%s" % sl(161, t - 1) if j > 0 else "161'b0"; ine = "ow%s" % sl(161, t + 1) if j < P - 1 else "161'b0"; inn = "os%s" % sl(161, (i - 1) * P + j) if i > 0 else "161'b0"; ins = "on%s" % sl(161, (i + 1) * P + j) if i < P - 1 else "161'b0"
            v.append("    mesh_tile_pipe #(.I(%d), .J(%d), .P(%d), .MT(%d), .NT(%d), .NBT(%d), .NP(%d), .FA(\"mesh_a_%d_%d.hex\"), .FB(\"mesh_b_%d_%d.hex\")) t%d (.clk(clk), .rst(rst), .go_comm(go_comm), .comm_prod(comm_prod), .comm_bank(comm_bank), .stop_comm(stop_comm), .go_comp(go_comp), .comp_prod(comp_prod), .comp_bank(comp_bank), .in_w(%s), .in_e(%s), .in_n(%s), .in_s(%s), .out_e(oe%s), .out_w(ow%s), .out_n(on%s), .out_s(os%s), .comm_done(cd[%d]), .comp_done(pd[%d]), .tx_a(ta%s), .tx_b(tb%s), .c_raddr(rd_idx), .c_macc(cmv%s), .c_eacc(cev%s));" % (i, j, P, MT, NT, NBT, NP, i, j, i, j, t, inw, ine, inn, ins, sl(161, t), sl(161, t), sl(161, t), sl(161, t), t, t, sl(32, t), sl(32, t), sl(17, t), sl(12, t)))
    nsteps = (NP + 1) if ovl else (2 * NP)
    v.append("    integer q; reg [31:0] sa, sb; always @(*) begin sa = 0; sb = 0; for (q = 0; q < %d; q = q + 1) begin sa = sa + ta[32*q +: 32]; sb = sb + tb[32*q +: 32]; end end" % T)
    v.append("    reg [3:0] st; reg [15:0] s; reg [3:0] dl; reg wc, wp; wire [15:0] sh = s >> 1;")
    if ovl: v.append("    wire dc = (s < %d), dp = (s >= 1); wire [7:0] cpr = s[7:0], kpr = s[7:0] - 8'd1;" % NP)
    else: v.append("    wire dc = (s[0] == 0), dp = (s[0] == 1); wire [7:0] cpr = sh[7:0], kpr = sh[7:0];")
    v.append("    always @(posedge clk) begin if (rst) begin st <= 0; done <= 0; go_comm <= 0; go_comp <= 0; stop_comm <= 0; cyc <= 0; s <= 0; end else begin go_comm <= 0; go_comp <= 0; stop_comm <= 0; done <= 0; if (st != 0) cyc <= cyc + 1; case (st) "
             "0: if (start) begin s <= 0; cyc <= 0; st <= 1; end "
             "1: begin wc <= dc; wp <= dp; if (dc) begin go_comm <= 1; comm_prod <= cpr; comm_bank <= cpr[0]; end if (dp) begin go_comp <= 1; comp_prod <= kpr; comp_bank <= kpr[0]; end dl <= 0; st <= 2; end "
             "2: begin dl <= dl + 1; if (dl == 3) st <= 3; end "
             "3: if ((!wc || &cd) && (!wp || &pd)) begin if (wc) stop_comm <= 1; if (s == %d) begin hops_a <= sa; hops_b <= sb; done <= 1; st <= 0; end else begin s <= s + 1; st <= 1; end end "
             "endcase end end" % (nsteps - 1))
    v.append("    always @(posedge clk) begin rd_macc <= cmv[17*rd_tile +: 17]; rd_eacc <= cev[12*rd_tile +: 12]; end"); v.append("endmodule")
    open(os.path.join(tmp, "mesh_top.v"), "w").write("\n".join(v) + "\n")
    tb = """`timescale 1ns/1ps
module mesh_tb; reg clk = 0, rst = 1, start = 0; wire done; wire [31:0] cc, ha, hb; reg [15:0] rt, ri; wire signed [16:0] rm; wire signed [11:0] re; integer f, t, k;
 mesh_top dut (.clk(clk), .rst(rst), .start(start), .done(done), .cyc(cc), .hops_a(ha), .hops_b(hb), .rd_tile(rt), .rd_idx(ri), .rd_macc(rm), .rd_eacc(re));
 always #5 clk = ~clk; initial begin repeat (3) @(posedge clk); rst = 0; @(negedge clk); start = 1; @(negedge clk); start = 0; wait (done); repeat (3) @(negedge clk); f = $fopen("out_mesh.txt", "w"); $fwrite(f, "cycles %0d hops %0d %0d\\n", cc, ha, hb);
  for (t = 0; t < NTILES; t = t + 1) for (k = 0; k < NELEM; k = k + 1) begin rt = t; ri = k; repeat (3) @(negedge clk); $fwrite(f, "%0d %0d\\n", rm, re); end $fclose(f); $finish; end endmodule
""".replace("NTILES", str(T)).replace("NELEM", str(NP * MT * NT))
    open(os.path.join(tmp, "mesh_tb.v"), "w").write(tb)
    subprocess.check_call(["iverilog", "-g2012", "-o", "sim", "mesh_tb.v", "mesh_top.v", "mesh_tile_pipe.v", "forge_lane.v"], cwd=tmp); subprocess.run(["timeout", "1500", "vvp", "sim"], cwd=tmp, capture_output=True, text=True)
    lines = open(os.path.join(tmp, "out_mesh.txt")).read().split("\n"); hdr = lines[0].split(); return int(hdr[1]), int(hdr[3]) + int(hdr[4]), [tuple(map(int, l.split())) for l in lines[1:] if l.strip()]
res = {}
for ovl in (0, 1):
    tmp = tempfile.mkdtemp(); cyc, hops, got = build(tmp, ovl); shutil.rmtree(tmp); bad = 0; worst = 0.0
    for tp, (A, B, ma, ea, mb, eb) in enumerate(prods):
        C = np.zeros((M, N))
        for i in range(P):
            for j in range(P):
                for m in range(MT):
                    for n in range(NT):
                        mm_, ee_ = 0, 0
                        for kb in range(KB): mm_, ee_ = lane_step(mm_, ee_, kb == 0, ma[i * MT + m, kb], mb[j * NT + n, kb], int(ea[i * MT + m, kb]), int(eb[j * NT + n, kb]))
                        g = got[(i * P + j) * NP * MT * NT + tp * MT * NT + m * NT + n]; bad += (g != (mm_, ee_)); C[i * MT + m, j * NT + n] = g[0] * 2.0 ** g[1]
        worst = max(worst, np.linalg.norm(C - A @ B) / np.linalg.norm(A @ B))
    res[ovl] = (cyc, hops, bad)
    print("%s: %d products, mesh %dx%d, C %dx%d, K %d: mismatches %d of %d outputs, worst error vs fp64 %.2e; cycles %d, link traversals %d" % ("OVERLAPPED" if ovl else "SEQUENTIAL", NP, P, P, M, N, K, bad, NP * M * N, worst, cyc, hops), flush=True)
s, o = res[0][0], res[1][0]; print("overlap saves %d cycles (%.1f%%): %d -> %d; per product %.0f -> %.0f; link traversals identical: %s" % (s - o, 100 * (s - o) / s, s, o, s / NP, o / NP, res[0][1] == res[1][1]))
print("PASS" if res[0][2] == 0 and res[1][2] == 0 else "FAIL"); sys.exit(0 if res[0][2] == 0 and res[1][2] == 0 else 1)
