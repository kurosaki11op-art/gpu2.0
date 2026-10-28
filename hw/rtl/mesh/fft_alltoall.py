"""FFT ALL-TO-ALL TEST. A distributed 2D DFT on a P x P mesh of tiles with GENERAL routers (hw/rtl/mesh/gr_tile.v: dimension-order routing, 4-flit input buffers, round-robin arbitration, back-pressure). N x N complex data, N = T * 4 rows per tile (T = P*P tiles). Phases: (1) each tile does its row DFTs, (2) block floating-point packing of the 4 x 4 sub-blocks, (3) ALL-TO-ALL TRANSPOSE through the mesh IN RTL (every tile sends one 4 x 4 complex block, two 136-bit flits, to every other tile), (4) each tile does its column DFTs. The DFT arithmetic runs in the bit-exact lane model (forge_tile_model.lane_matmul, as an earlier note validated against the lane RTL); the transpose is the RTL under test. Checks: every received word equals the intended word; the final result equals the same pipeline computed without the mesh; its error against numpy's fft2; and the network cost: cycles against the bisection bandwidth bound, link traversals per flit against the mean Manhattan distance the traffic model assumed, latency, blocked cycles. SIMULATED. Usage: python fft_alltoall.py [P]  (P = 2, 4 or 8)"""
import os, shutil, subprocess, sys, tempfile
import numpy as np
here = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(here, "..", "..", "brain", "experiments", "month5"))
from forge_tile_model import bfp_encode, lane_matmul
P = int(sys.argv[1]) if len(sys.argv) > 1 else 4; T = P * P; R = 4; N = T * R; rs = np.random.RandomState(P)
def dft_real(n): k = np.arange(n); W = np.exp(-2j * np.pi * np.outer(k, k) / n); return np.block([[W.real, -W.imag], [W.imag, W.real]])
F = dft_real(N)
def dft_cols(Z):                                                  # Z: (N, c) complex, DFT of every column through the lane model
    C = lane_matmul(F, np.vstack([Z.real, Z.imag]))[0]; return C[:N] + 1j * C[N:]
def pack(vals):                                                   # 16 real values -> one BFP word (136 bits) and the decoded values
    m, e = bfp_encode(vals.reshape(1, 16)); m = m[0, 0]; e = int(e[0, 0]); w = ((e & 255) << 128) | sum((int(v) & 255) << (8 * k) for k, v in enumerate(m)); return w, m * 2.0 ** (e - 6)
X = rs.randn(N, N) + 1j * rs.randn(N, N); Y = np.zeros((N, N), complex)
for s in range(T): Y[s * R:(s + 1) * R, :] = dft_cols(X[s * R:(s + 1) * R, :].T).T       # row DFTs of tile s (rows s*R..s*R+R-1)
words = {}; Yq = np.zeros((N, N), complex)                        # words[(s, d, k)] intended payload; Yq = the row-DFT data as it exists after packing
for s in range(T):
    for d in range(T):
        sub = Y[s * R:(s + 1) * R, d * R:(d + 1) * R]; wr, vr = pack(sub.real.reshape(16)); wi, vi = pack(sub.imag.reshape(16)); words[(s, d, 0)] = wr; words[(s, d, 1)] = wi
        Yq[s * R:(s + 1) * R, d * R:(d + 1) * R] = vr.reshape(R, R) + 1j * vi.reshape(R, R)
golden = np.zeros((N, N), complex)
for d in range(T): golden[:, d * R:(d + 1) * R] = dft_cols(Yq[:, d * R:(d + 1) * R])                # column DFTs of tile d on the intended data
tmp = tempfile.mkdtemp(); shutil.copy(os.path.join(here, "gr_tile.v"), tmp); NI = (T - 1) * 2; NSLOT = T * 2
for s in range(T):
    lines = []
    for d in range(T):
        if d == s: continue
        for k in range(2): lines.append("%02x%02x%04x%04x%034x" % (d % P, d // P, s * 2 + k, 0, words[(s, d, k)]))
    open(os.path.join(tmp, "inj_%d_%d.hex" % (s // P, s % P)), "w").write("\n".join(lines) + "\n")
v = ["module gr_top (input clk, input rst, input go, output done_all, output [31:0] hops, output [31:0] waits, output [31:0] lats, output [31:0] recvs, input [15:0] rd_tile, input [15:0] rd_slot, output reg [135:0] rd_data);"]
for t in range(T): v.append("    wire nv%d, ev%d, sv%d, wv%d, nr%d, er%d, sr%d, wr%d, dn%d; wire [183:0] nf%d, ef%d, sf%d, wf%d; wire [31:0] h%d, w%d, l%d, r%d; wire [135:0] rd%d;" % ((t,) * 5 + (t,) * 4 + (t,) * 5 + (t,) * 4 + (t,)) if False else "    wire nv%d, ev%d, sv%d, wv%d, nr%d, er%d, sr%d, wr%d, dn%d; wire [183:0] nf%d, ef%d, sf%d, wf%d; wire [31:0] h%d, w%d, l%d, r%d; wire [135:0] rd%d;" % tuple([t] * 18))
for i in range(P):
    for j in range(P):
        t = i * P + j; nb = lambda di, dj: (i + di) * P + (j + dj) if 0 <= i + di < P and 0 <= j + dj < P else None
        up, rt, dn, lf = nb(-1, 0), nb(0, 1), nb(1, 0), nb(0, -1)
        # my in_n comes from the tile above's out_s; its ready tells the tile above (my out_n target is the tile above: its rdy_s)
        v.append("    gr_tile #(.X(%d), .Y(%d), .NI(%d), .NSLOT(%d), .EXPECT(%d), .FILE_INJ(\"inj_%d_%d.hex\")) u%d (.clk(clk), .rst(rst), .go(go), .in_n_v(%s), .in_n_f(%s), .rdy_n(nr%d), .in_e_v(%s), .in_e_f(%s), .rdy_e(er%d), .in_s_v(%s), .in_s_f(%s), .rdy_s(sr%d), .in_w_v(%s), .in_w_f(%s), .rdy_w(wr%d), .out_n_v(nv%d), .out_n_f(nf%d), .ord_n(%s), .out_e_v(ev%d), .out_e_f(ef%d), .ord_e(%s), .out_s_v(sv%d), .out_s_f(sf%d), .ord_s(%s), .out_w_v(wv%d), .out_w_f(wf%d), .ord_w(%s), .done(dn%d), .cnt_hops(h%d), .cnt_wait(w%d), .lat_sum(l%d), .recv_n(r%d), .rd_slot(rd_slot[%d:0]), .rd_data(rd%d));" % (
            j, i, NI, NSLOT, NI, i, j, t, "sv%d" % up if up is not None else "1'b0", "sf%d" % up if up is not None else "184'b0", t, "wv%d" % rt if rt is not None else "1'b0", "wf%d" % rt if rt is not None else "184'b0", t, "nv%d" % dn if dn is not None else "1'b0", "nf%d" % dn if dn is not None else "184'b0", t, "ev%d" % lf if lf is not None else "1'b0", "ef%d" % lf if lf is not None else "184'b0", t,
            t, t, ("sr%d" % up) if up is not None else "1'b0", t, t, ("wr%d" % rt) if rt is not None else "1'b0", t, t, ("nr%d" % dn) if dn is not None else "1'b0", t, t, ("er%d" % lf) if lf is not None else "1'b0", t, t, t, t, t, NSLOT.bit_length() - 1, t))
v.append("    assign done_all = &{%s}; assign hops = %s; assign waits = %s; assign lats = %s; assign recvs = %s;" % (", ".join("dn%d" % t for t in range(T)), " + ".join("h%d" % t for t in range(T)), " + ".join("w%d" % t for t in range(T)), " + ".join("l%d" % t for t in range(T)), " + ".join("r%d" % t for t in range(T))))
v.append("    always @(*) begin case (rd_tile) " + " ".join("%d: rd_data = rd%d;" % (t, t) for t in range(T)) + " default: rd_data = 0; endcase end")
v.append("endmodule"); open(os.path.join(tmp, "gr_top.v"), "w").write("\n".join(v) + "\n")
tb = """`timescale 1ns/1ps
module gr_tb; reg clk = 0, rst = 1, go = 0; wire done_all; wire [31:0] hops, waits, lats, recvs; reg [15:0] rt, rs_; wire [135:0] rd; integer f, t, s, cyc;
 gr_top dut (.clk(clk), .rst(rst), .go(go), .done_all(done_all), .hops(hops), .waits(waits), .lats(lats), .recvs(recvs), .rd_tile(rt), .rd_slot(rs_), .rd_data(rd));
 always #5 clk = ~clk; initial begin repeat (3) @(posedge clk); rst = 0; @(negedge clk); go = 1; @(negedge clk); go = 0; cyc = 0; while (!done_all && cyc < 200000) begin @(negedge clk); cyc = cyc + 1; end
  f = $fopen("out_gr.txt", "w"); $fwrite(f, "%0d %0d %0d %0d %0d\\n", cyc, hops, waits, lats, recvs);
  for (t = 0; t < NT; t = t + 1) for (s = 0; s < NS; s = s + 1) begin rt = t; rs_ = s; #1; $fwrite(f, "%h\\n", rd); end $fclose(f); $finish; end endmodule
""".replace("NT", str(T)).replace("NS", str(NSLOT))
open(os.path.join(tmp, "gr_tb.v"), "w").write(tb)
subprocess.check_call(["iverilog", "-g2012", "-o", "sim", "gr_tb.v", "gr_top.v", "gr_tile.v"], cwd=tmp); subprocess.run(["timeout", "900", "vvp", "sim"], cwd=tmp, capture_output=True)
L = open(os.path.join(tmp, "out_gr.txt")).read().split("\n"); cyc, hops, waits, lats, recvs = map(int, L[0].split()); dat = [int(l, 16) if 'x' not in l and 'z' not in l else 0 for l in L[1:] if l.strip()]
bad = 0; Yr = np.zeros((N, N), complex)
for d in range(T):
    for s in range(T):
        if s == d: wr_, wi_ = words[(s, d, 0)], words[(s, d, 1)]
        else: wr_, wi_ = dat[d * NSLOT + s * 2], dat[d * NSLOT + s * 2 + 1]; bad += (wr_ != words[(s, d, 0)]) + (wi_ != words[(s, d, 1)])
        dec = lambda w: np.array([((w >> (8 * k)) & 255) - 256 if ((w >> (8 * k)) & 128) else ((w >> (8 * k)) & 255) for k in range(16)]) * 2.0 ** (((w >> 128) & 255) - 256 + 0 if ((w >> 128) & 128) else ((w >> 128) & 255)) * 2.0 ** -6
        Yr[s * R:(s + 1) * R, d * R:(d + 1) * R] = dec(wr_).reshape(R, R) + 1j * dec(wi_).reshape(R, R)
Z = np.zeros((N, N), complex)
for d in range(T): Z[:, d * R:(d + 1) * R] = dft_cols(Yr[:, d * R:(d + 1) * R])
same = np.array_equal(Z, golden); err = np.linalg.norm(Z - np.fft.fft2(X)) / np.linalg.norm(np.fft.fft2(X))
flits = T * NI; dist = np.mean([abs(a % P - b % P) + abs(a // P - b // P) for a in range(T) for b in range(T) if a != b]); bound = max((T // 2) * (T // 2) * 2 // P, NI)
print("mesh %dx%d (%d tiles), 2D DFT %dx%d, all-to-all transpose: %d flits (136-bit block words)" % (P, P, T, N, N, flits))
print("  delivery: %d of %d words differ from the intended words; final result identical to the same pipeline without the mesh: %s; error vs numpy fft2 %.2e" % (bad, T * NI, same, err))
print("  network: %d cycles (lower bound %d = the larger of the bisection-bandwidth bound and one flit per cycle injection -> %.0f%% of the best possible); link traversals %d = %.2f per flit (mean Manhattan distance between distinct tiles %.2f); mean latency %.1f cycles; blocked flit-cycles %d (%.1f per flit)" % (cyc, bound, 100 * bound / cyc, hops, hops / flits, dist, lats / recvs, waits, waits / flits))
shutil.rmtree(tmp); sys.exit(1 if (bad or not same or recvs != flits) else 0)
