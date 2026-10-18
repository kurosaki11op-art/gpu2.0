// SPARK Cortex sensory encoder: 28x28 image -> sorted list of active code bits, bit-exact with
// hw/brain/feature_layer.py (Features.encode for the channels (50, 150, ('on', 8), ('off', 8)), F = 32, pool 2).
// No multiplier: compares, adds, shifts, XOR and bit counts only.
//
//   receptors : ch0 = pixel > 50, ch1 = pixel > 150,
//               ch2 = pixel - (sum of 8 neighbours >> 3) > 8 (ON cell), ch3 = (sum >> 3) - pixel > 8 (OFF cell);
//               image edges repeat the border pixel
//   detectors : 5x5 windows at stride 2 (12 x 12 spots); per channel the detector (of 32) with the most agreeing bits
//               wins (first one on a tie); a window with fewer than 3 on bits stays silent
//   pooling   : 2x2 spots -> 6x6 cells; code bit = ch*1152 + (cell_row*6 + cell_col)*32 + detector
//   output    : the active code bits in increasing order, written through the core's list write port
// Build option ENC_S1 (finer winner grid, 19 Oct 2026, bit-exact with Features(32, pool=4) and feature_layer.PS, ST = 5, 1): 5x5 windows at
// stride 1 (24 x 24 spots), pooling 4 x 4 spots -> the same 6 x 6 cells and 4,608 code bits, 2.3x the encoder cycles (48,162 vs 21,378 per image). Clothing +4.6 all at once,
// digits +0.7 all at once but -1.4 in 5 stages (note slow_table_and_staged_limits.md). Not combined with ENC_LEARN.
// Load the image with pix_we, the detectors with tm_we (tm_ch, tm_f, 25 bits; bit r*5+c = window row r, column c),
// then pulse start; done pulses with the list length in count.
//
// Build option ENC_LEARN (`define ENC_LEARN): the encoder learns its own detectors from the images it sees, without
// labels (bit-exact with hw/brain/detector_learn.py). Per channel 32 detectors x 25 six-bit counters; tm* hold their
// signs. lclear (idle) restarts learning; start with learn = 1 learns from the loaded image instead of encoding it
// (done, count 0): each non-blank window first seeds the next unseeded detector, later moves the winner's counters one
// step toward it (clip +-31), marks the winner and enters a ring of the last 32 windows; reseed (idle) gives every
// detector that has not won since the last reseed the next window from the ring. Costs 19,200 + 3,200 + 128 bits of
// state and one add/clip per bit of the winner; meant for the ASIC (the Tang Nano build is full).
`timescale 1ns/1ps
`ifdef ENC_S1
`ifdef ENC_LEARN
`error "ENC_S1 cannot be combined with ENC_LEARN"
`endif
`endif
module cortex_encoder #(parameter AW = 13) (
    input  wire          clk, rst,
    input  wire          pix_we, input wire [9:0] pix_addr, input wire [7:0] pix_data,
    input  wire          tm_we, input wire [1:0] tm_ch, input wire [4:0] tm_f, input wire [24:0] tm_data,
    input  wire          start,
`ifdef ENC_LEARN
    input  wire          learn, lclear, reseed,
`endif
    output reg           busy, output reg done, output reg [AW:0] count,
    output reg           out_we, output reg [AW-1:0] out_addr, output reg [AW-1:0] out_data
);
    reg [7:0]  pix  [0:783];
    reg [3:0]  bmap [0:783];
    reg [24:0] tm0 [0:31], tm1 [0:31], tm2 [0:31], tm3 [0:31];
`ifdef CORTEX_ASIC
    reg        cmap [0:4607];
`else
    reg  [3:0] cmap4 [0:1151];                  // FPGA: code map packed 4 bits per word (fills the small LUT RAMs)
`endif
    integer t;
`ifdef CORTEX_ASIC
    initial for (t = 0; t < 4608; t = t + 1) cmap[t] = 1'b0;   // power-up zero; EMIT re-clears it
`else
    initial for (t = 0; t < 1152; t = t + 1) cmap4[t] = 4'b0;  // power-up zero (FPGA RAM starts cleared); EMIT re-clears it
`endif

`ifdef CORTEX_ASIC
    // ASIC build: each flip-flop memory gets its own gated clock, running only in cycles that write it (an idle
    // memory then costs no clock power); the FPGA build is unchanged.
    wire ck_pix, ck_tm;
    cortex_cg g_pix (.clk(clk), .en(pix_we), .gclk(ck_pix));
    cortex_cg g_tm (.clk(clk), .en(tm_we), .gclk(ck_tm));
`else
    wire ck_pix = clk, ck_tm = clk;
`endif
    always @(posedge ck_pix) if (pix_we) pix[pix_addr] <= pix_data;
`ifndef ENC_LEARN
    always @(posedge ck_tm) if (tm_we) case (tm_ch)
        2'd0: tm0[tm_f] <= tm_data; 2'd1: tm1[tm_f] <= tm_data; 2'd2: tm2[tm_f] <= tm_data; default: tm3[tm_f] <= tm_data;
    endcase
`else
    reg [149:0] lc [0:127];                     // counters, index {channel, detector}; 6 bits per window bit
    reg [24:0]  ring [0:127];                   // last 32 learned windows per channel, index {channel, slot}
    reg [127:0] won;                            // detector won since the last reseed
    reg [5:0]   seeded [0:3];                   // detectors seeded per channel (0..32)
    reg [4:0]   rp [0:3], kk [0:3];             // ring write position, reseed read position
    reg         lmode; reg [4:0] r;
    initial for (t = 0; t < 128; t = t + 1) begin lc[t] = 0; ring[t] = 0; end
    function [149:0] seedw; input [24:0] v; integer q; begin
        for (q = 0; q < 25; q = q + 1) seedw[q*6 +: 6] = v[q] ? 6'd1 : 6'h3f;
    end endfunction
    function [149:0] stepw; input [149:0] c; input [24:0] v; integer q; reg signed [6:0] x; begin
        for (q = 0; q < 25; q = q + 1) begin
            x = $signed(c[q*6 +: 6]) + (v[q] ? 7'sd1 : -7'sd1);
            stepw[q*6 +: 6] = (x > 31) ? 6'd31 : (x < -31) ? 6'h21 : x[5:0];
        end
    end endfunction
    function [24:0] signs; input [149:0] c; integer q; begin
        for (q = 0; q < 25; q = q + 1) signs[q] = ~c[q*6 + 5];
    end endfunction
`endif

    function [4:0] pop25; input [24:0] v; integer q; begin
        pop25 = 0; for (q = 0; q < 25; q = q + 1) pop25 = pop25 + v[q];
    end endfunction

    localparam E_IDLE = 0, E_BIN = 1, E_BIN2 = 2, E_POS = 3, E_GATH = 4, E_MATCH = 5, E_SET = 6, E_EMIT = 7, E_DONE = 8,
               E_LRN = 9, E_RSD = 10;
    reg [3:0] st;
    // receptor stage
    reg [4:0] py, pxx; reg [1:0] ky, kx; reg [11:0] nsum; reg [7:0] ctr;
    // detector stage
    reg [4:0] si, sj; reg [4:0] g; reg [2:0] gr, gc; reg [24:0] p0, p1, p2, p3; reg [5:0] f;
    reg [4:0] b0, b1, b2, b3; reg [4:0] w0, w1, w2, w3; reg [1:0] sc;
    reg [12:0] e; reg [AW:0] k;
    // x * 28 and x * 6 as shifts and adds (no multiplier)
    function [9:0] m28; input [4:0] v; begin m28 = {v, 4'b0} + {v, 3'b0} + {v, 2'b0}; end endfunction
    // neighbour (ky, kx) in 0..2 of pixel (py, pxx), (1, 1) = centre; image edges clamped
    wire [4:0] cy = (ky == 0) ? ((py == 0) ? 5'd0 : py - 1'b1) : (ky == 2) ? ((py == 27) ? 5'd27 : py + 1'b1) : py;
    wire [4:0] cx = (kx == 0) ? ((pxx == 0) ? 5'd0 : pxx - 1'b1) : (kx == 2) ? ((pxx == 27) ? 5'd27 : pxx + 1'b1) : pxx;
    wire [7:0] nval = pix[m28(cy) + cx];
    wire [8:0] avg = nsum[11:3];
    wire [3:0] bmap_v = {($signed({1'b0, avg}) - $signed({1'b0, ctr}) > 8), ($signed({1'b0, ctr}) - $signed({1'b0, avg}) > 8),
                         ctr > 150, ctr > 50};
    // window cell (gr, gc) of spot (si, sj)
`ifdef ENC_S1
    wire [4:0] wy = si + gr, wx = sj + gc;
    localparam [4:0] SLAST = 5'd23;
`else
    wire [4:0] wy = {si, 1'b0} + gr, wx = {sj, 1'b0} + gc;
    localparam [4:0] SLAST = 5'd11;
`endif
    wire [3:0] gb = bmap[m28(wy) + wx];
    wire [4:0] a0 = pop25(~(p0 ^ tm0[f[4:0]])), a1 = pop25(~(p1 ^ tm1[f[4:0]])),
               a2 = pop25(~(p2 ^ tm2[f[4:0]])), a3 = pop25(~(p3 ^ tm3[f[4:0]]));
    wire [4:0] wsel = (sc == 0) ? w0 : (sc == 1) ? w1 : (sc == 2) ? w2 : w3;
    wire [24:0] psel = (sc == 0) ? p0 : (sc == 1) ? p1 : (sc == 2) ? p2 : p3;
    wire       osel = (sc == 0) ? (pop25(p0) >= 3) : (sc == 1) ? (pop25(p1) >= 3) : (sc == 2) ? (pop25(p2) >= 3) : (pop25(p3) >= 3);
`ifdef ENC_S1
    wire [2:0] ci = si[4:2], cj = sj[4:2];
`else
    wire [2:0] ci = si[3:1], cj = sj[3:1];
`endif
    wire [5:0] pcell = {ci, 2'b0} + {ci, 1'b0} + cj;                                  // ci * 6 + cj
    wire [12:0] cidx = {sc, 10'b0} + {sc, 7'b0} + {pcell, 5'b0} + wsel;                // sc * 1152 + cell * 32 + detector
`ifdef CORTEX_ASIC
    wire       cbit = cmap[e];
`else
    wire [3:0] cword = cmap4[e[12:2]];
    wire       cbit = cword[e[1:0]];
`endif
`ifdef CORTEX_ASIC
    wire ck_bmap, ck_cmap;
    wire bmap_wr = (st == E_BIN2), cmap_set = (st == E_SET) && osel, cmap_clr = (st == E_EMIT) && cmap[e];
    cortex_cg g_bmap (.clk(clk), .en(bmap_wr), .gclk(ck_bmap));
    cortex_cg g_cmap (.clk(clk), .en(cmap_set | cmap_clr), .gclk(ck_cmap));
    always @(posedge ck_bmap) bmap[m28(py) + pxx] <= bmap_v;
    always @(posedge ck_cmap) if (cmap_set) cmap[cidx] <= 1'b1; else cmap[e] <= 1'b0;
`endif

    always @(posedge clk) begin
        done <= 0; out_we <= 0;
        if (rst) begin st <= E_IDLE; busy <= 0; end
        else case (st)
        E_IDLE: begin
            if (start) begin busy <= 1; py <= 0; pxx <= 0; ky <= 0; kx <= 0; nsum <= 0; st <= E_BIN; end
`ifdef ENC_LEARN
            lmode <= learn;
            if (tm_we) case (tm_ch)
                2'd0: tm0[tm_f] <= tm_data; 2'd1: tm1[tm_f] <= tm_data; 2'd2: tm2[tm_f] <= tm_data; default: tm3[tm_f] <= tm_data;
            endcase
            if (lclear) begin
                won <= 0; for (t = 0; t < 4; t = t + 1) begin seeded[t] <= 0; rp[t] <= 0; end
            end
            if (reseed && !start) begin
                busy <= 1; r <= 0; for (t = 0; t < 4; t = t + 1) kk[t] <= 0; st <= E_RSD;
            end
`endif
        end
        // ---- receptors: walk the 9 neighbours of each pixel ------------------------------------------------------
        E_BIN: begin
            if (ky == 1 && kx == 1) ctr <= nval; else nsum <= nsum + nval;
            if (kx == 2) begin kx <= 0; if (ky == 2) st <= E_BIN2; else ky <= ky + 1'b1; end
            else kx <= kx + 1'b1;
        end
        E_BIN2: begin
`ifndef CORTEX_ASIC
            bmap[m28(py) + pxx] <= bmap_v;
`endif
            ky <= 0; kx <= 0; nsum <= 0; st <= E_BIN;
            if (pxx == 27) begin
                pxx <= 0;
                if (py == 27) begin si <= 0; sj <= 0; st <= E_POS; end else py <= py + 1;
            end else pxx <= pxx + 1;
        end
        // ---- detectors: gather the 5x5 window of the 4 channels, then match 32 detectors per channel ---------------
        E_POS: begin g <= 0; gr <= 0; gc <= 0; st <= E_GATH; end
        E_GATH: begin
            p0[g] <= gb[0]; p1[g] <= gb[1]; p2[g] <= gb[2]; p3[g] <= gb[3];
            if (g == 24) begin f <= 0; b0 <= 0; b1 <= 0; b2 <= 0; b3 <= 0; w0 <= 0; w1 <= 0; w2 <= 0; w3 <= 0; st <= E_MATCH; end
            else begin g <= g + 1'b1; if (gc == 4) begin gc <= 0; gr <= gr + 1'b1; end else gc <= gc + 1'b1; end
        end
        E_MATCH: begin
            if (f == 0 || a0 > b0) begin b0 <= a0; w0 <= f[4:0]; end
            if (f == 0 || a1 > b1) begin b1 <= a1; w1 <= f[4:0]; end
            if (f == 0 || a2 > b2) begin b2 <= a2; w2 <= f[4:0]; end
            if (f == 0 || a3 > b3) begin b3 <= a3; w3 <= f[4:0]; end
`ifdef ENC_LEARN
            if (f == 31) begin sc <= 0; st <= lmode ? E_LRN : E_SET; end else f <= f + 1;
`else
            if (f == 31) begin sc <= 0; st <= E_SET; end else f <= f + 1;
`endif
        end
        E_SET: begin
`ifndef CORTEX_ASIC
            if (osel) cmap4[cidx[12:2]] <= cmap4[cidx[12:2]] | (4'b1 << cidx[1:0]);
`endif
            if (sc == 3) begin
                if (sj == SLAST) begin
                    sj <= 0;
                    if (si == SLAST) begin e <= 0; k <= 0; st <= E_EMIT; end else begin si <= si + 1; st <= E_POS; end
                end else begin sj <= sj + 1; st <= E_POS; end
            end else sc <= sc + 1;
        end
        // ---- emit the active code bits in order, clearing the map for the next image --------------------------------
        E_EMIT: begin
            if (cbit) begin
                out_we <= 1; out_addr <= k[AW-1:0]; out_data <= e; k <= k + 1;
`ifndef CORTEX_ASIC
                cmap4[e[12:2]] <= cmap4[e[12:2]] & ~(4'b1 << e[1:0]);
`endif
            end
            if (e == 4607) st <= E_DONE; else e <= e + 1;
        end
        E_DONE: begin count <= k; done <= 1; busy <= 0; st <= E_IDLE; end
`ifdef ENC_LEARN
        // ---- learning: one channel per cycle, the window of channel sc against its winner wsel -------------------
        E_LRN: begin
            if (osel) begin
                if (seeded[sc] != 32) begin
                    lc[{sc, seeded[sc][4:0]}] <= seedw(psel);
                    case (sc) 2'd0: tm0[seeded[0][4:0]] <= psel; 2'd1: tm1[seeded[1][4:0]] <= psel;
                              2'd2: tm2[seeded[2][4:0]] <= psel; default: tm3[seeded[3][4:0]] <= psel; endcase
                    seeded[sc] <= seeded[sc] + 1'b1;
                end else begin
                    lc[{sc, wsel}] <= stepw(lc[{sc, wsel}], psel);
                    case (sc) 2'd0: tm0[wsel] <= signs(stepw(lc[{sc, wsel}], psel)); 2'd1: tm1[wsel] <= signs(stepw(lc[{sc, wsel}], psel));
                              2'd2: tm2[wsel] <= signs(stepw(lc[{sc, wsel}], psel)); default: tm3[wsel] <= signs(stepw(lc[{sc, wsel}], psel)); endcase
                    won[{sc, wsel}] <= 1'b1;
                    ring[{sc, rp[sc]}] <= psel; rp[sc] <= rp[sc] + 1'b1;
                end
            end
            if (sc == 3) begin
                if (sj == SLAST) begin
                    sj <= 0;
                    if (si == SLAST) begin k <= 0; st <= E_DONE; end else begin si <= si + 1; st <= E_POS; end
                end else begin sj <= sj + 1; st <= E_POS; end
            end else sc <= sc + 1;
        end
        // ---- reseed: detector r of every channel that has not won takes the next ring window ------------------------
        E_RSD: begin
            for (t = 0; t < 4; t = t + 1) if (!won[t*32 + r]) begin
                lc[t*32 + r] <= seedw(ring[t*32 + kk[t]]); kk[t] <= kk[t] + 1'b1;
            end
            if (!won[r])      tm0[r] <= ring[kk[0]];
            if (!won[32 + r]) tm1[r] <= ring[32 + kk[1]];
            if (!won[64 + r]) tm2[r] <= ring[64 + kk[2]];
            if (!won[96 + r]) tm3[r] <= ring[96 + kk[3]];
            if (r == 31) begin won <= 0; for (t = 0; t < 4; t = t + 1) rp[t] <= 0; busy <= 0; done <= 1; count <= 0; st <= E_IDLE; end
            else r <= r + 1'b1;
        end
`endif
        default: st <= E_IDLE;
        endcase
    end
endmodule
