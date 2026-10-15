// SPARK Cortex sensory encoder, general version: any number of receptor channels and detectors per channel, for
// images (4 channels x 32 detectors, 4,608-bit code) and sound pictures (10 channels x 64 detectors, 23,040 bits).
// Bit-exact with hw/brain/feature_layer.py (Features.encode per channel, codes concatenated channel after channel).
// No multiplier: compares, adds, shifts, XOR and bit counts.
//
//   receptors : channel c is either "brighter than THR[c]" (KIND 0), an ON cell (KIND 1: pixel - (sum of 8
//               neighbours >> 3) > THR[c]) or an OFF cell (KIND 2: (sum >> 3) - pixel > THR[c]); edges repeat
//   detectors : 5x5 windows at stride 2 (12 x 12 spots); per channel the detector with the most agreeing bits wins
//               (first one on a tie); a window with fewer than 3 on bits stays silent. One channel at a time.
//   pooling   : 2x2 spots -> 6x6 cells; code bit = c*36*F + (cell_row*6 + cell_col)*F + detector
//   output    : the active code bits in increasing order, through the core's list write port
// Load the picture with pix_we and the detectors with tm_we (tm_addr = c*F + detector, 25 bits; bit r*5+col), then
// pulse start; done pulses with the list length in count. ~144 x NCH x (F + 30) cycles per picture.
`timescale 1ns/1ps
module cortex_encoder_gen #(
    parameter NCH = 4, parameter F = 32, parameter LF = 5,              // LF = log2(F)
    parameter [8*NCH-1:0] THR = {8'd8, 8'd8, 8'd150, 8'd50},            // channel c at [8c +: 8]
    parameter [2*NCH-1:0] KIND = {2'd2, 2'd1, 2'd0, 2'd0},              // channel c at [2c +: 2]
    parameter AW = 15
) (
    input  wire          clk, rst,
    input  wire          pix_we, input wire [9:0] pix_addr, input wire [7:0] pix_data,
    input  wire          tm_we, input wire [LF+3:0] tm_addr, input wire [24:0] tm_data,
    input  wire          start,
    output reg           busy, output reg done, output reg [AW:0] count,
    output reg           out_we, output reg [AW-1:0] out_addr, output reg [AW-1:0] out_data
);
    localparam NB = NCH * 36 * F, CB = 36 * F;
    reg [7:0]     pix  [0:783];
    reg [NCH-1:0] bmap [0:783];
    reg [24:0]    tm   [0:NCH*F-1];
    reg           cmap [0:NB-1];
    integer t;
    initial for (t = 0; t < NB; t = t + 1) cmap[t] = 1'b0;
    always @(posedge clk) if (pix_we) pix[pix_addr] <= pix_data;
    always @(posedge clk) if (tm_we) tm[tm_addr] <= tm_data;

    function [4:0] pop25; input [24:0] v; integer q; begin
        pop25 = 0; for (q = 0; q < 25; q = q + 1) pop25 = pop25 + v[q];
    end endfunction
    function [9:0] m28; input [4:0] v; begin m28 = {v, 4'b0} + {v, 3'b0} + {v, 2'b0}; end endfunction

    localparam E_IDLE = 0, E_BIN = 1, E_BIN2 = 2, E_POS = 3, E_GATH = 4, E_MATCH = 5, E_SET = 6, E_EMIT = 7, E_DONE = 8;
    reg [3:0] st;
    reg [4:0] py, pxx; reg [1:0] ky, kx; reg [11:0] nsum; reg [7:0] ctr;
    reg [3:0] si, sj; reg [4:0] g; reg [2:0] gr, gc; reg [24:0] p; reg [LF:0] f; reg [4:0] bst; reg [LF-1:0] w;
    reg [3:0] ch; reg [AW:0] e; reg [AW:0] k;
    wire [4:0] cy = (ky == 0) ? ((py == 0) ? 5'd0 : py - 1'b1) : (ky == 2) ? ((py == 27) ? 5'd27 : py + 1'b1) : py;
    wire [4:0] cx = (kx == 0) ? ((pxx == 0) ? 5'd0 : pxx - 1'b1) : (kx == 2) ? ((pxx == 27) ? 5'd27 : pxx + 1'b1) : pxx;
    wire [7:0] nval = pix[m28(cy) + cx];
    wire [8:0] avg = nsum[11:3];
    // receptor bits of the current pixel, all channels
    reg [NCH-1:0] rb; integer c2;
    always @(*) for (c2 = 0; c2 < NCH; c2 = c2 + 1)
        case (KIND[2*c2 +: 2])
            2'd1: rb[c2] = $signed({1'b0, ctr}) - $signed({1'b0, avg}) > $signed({1'b0, THR[8*c2 +: 8]});
            2'd2: rb[c2] = $signed({1'b0, avg}) - $signed({1'b0, ctr}) > $signed({1'b0, THR[8*c2 +: 8]});
            default: rb[c2] = ctr > THR[8*c2 +: 8];
        endcase
    wire [4:0] wy = {si, 1'b0} + gr, wx = {sj, 1'b0} + gc;
    wire [NCH-1:0] gb = bmap[m28(wy) + wx];
    wire [4:0] a = pop25(~(p ^ tm[ch * F + f[LF-1:0]]));
    wire [2:0] ci = si[3:1], cj = sj[3:1];
    wire [5:0] pcell = {ci, 2'b0} + {ci, 1'b0} + cj;                       // ci * 6 + cj
    wire [AW-1:0] cidx = ch * CB + pcell * F + w;                         // constant multiplies: shifts and adds

    always @(posedge clk) begin
        done <= 0; out_we <= 0;
        if (rst) begin st <= E_IDLE; busy <= 0; end
        else case (st)
        E_IDLE: if (start) begin busy <= 1; py <= 0; pxx <= 0; ky <= 0; kx <= 0; nsum <= 0; st <= E_BIN; end
        E_BIN: begin
            if (ky == 1 && kx == 1) ctr <= nval; else nsum <= nsum + nval;
            if (kx == 2) begin kx <= 0; if (ky == 2) st <= E_BIN2; else ky <= ky + 1'b1; end
            else kx <= kx + 1'b1;
        end
        E_BIN2: begin
            bmap[m28(py) + pxx] <= rb;
            ky <= 0; kx <= 0; nsum <= 0; st <= E_BIN;
            if (pxx == 27) begin
                pxx <= 0;
                if (py == 27) begin si <= 0; sj <= 0; ch <= 0; st <= E_POS; end else py <= py + 1;
            end else pxx <= pxx + 1;
        end
        E_POS: begin g <= 0; gr <= 0; gc <= 0; st <= E_GATH; end
        E_GATH: begin
            p[g] <= gb[ch];
            if (g == 24) begin f <= 0; bst <= 0; w <= 0; st <= E_MATCH; end
            else begin g <= g + 1'b1; if (gc == 4) begin gc <= 0; gr <= gr + 1'b1; end else gc <= gc + 1'b1; end
        end
        E_MATCH: begin
            if (f == 0 || a > bst) begin bst <= a; w <= f[LF-1:0]; end
            if (f == F - 1) st <= E_SET; else f <= f + 1'b1;
        end
        E_SET: begin
            if (pop25(p) >= 3) cmap[cidx] <= 1'b1;
            if (ch == NCH - 1) begin
                ch <= 0;
                if (sj == 11) begin
                    sj <= 0;
                    if (si == 11) begin e <= 0; k <= 0; st <= E_EMIT; end else begin si <= si + 1; st <= E_POS; end
                end else begin sj <= sj + 1; st <= E_POS; end
            end else begin ch <= ch + 1'b1; st <= E_POS; end
        end
        E_EMIT: begin
            if (cmap[e]) begin out_we <= 1; out_addr <= k[AW-1:0]; out_data <= e[AW-1:0]; k <= k + 1; cmap[e] <= 1'b0; end
            if (e == NB - 1) st <= E_DONE; else e <= e + 1;
        end
        E_DONE: begin count <= k; done <= 1; busy <= 0; st <= E_IDLE; end
        default: st <= E_IDLE;
        endcase
    end
endmodule
