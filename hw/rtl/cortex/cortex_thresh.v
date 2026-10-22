// SPARK Cortex threshold units (22 Oct 2026): the thresholds the host used to compute are now found by the chip from its own unlabelled margins. Compares, adds and shifts only.
// cortex_quant: streaming quantile tracker. q starts at the first sample; for every further sample x: if x < q then q = q - ((16 - n) << e) else q = q + (n << e), saturated to 0 .. 2^W - 1; the step shift e = max(EMIN, E0 - (count >> K)) shrinks as samples arrive.
//   Stationary point: the share of samples below q is n/16 (n = 3 -> the 19 % least-sure inputs get the second look; n = 8 -> the median, the reference of the cue-weighting unit).
// cortex_cuethr: the 7 cue-weighting thresholds ref * 2^(k - 0.5), k = -3..3, from ref: h = (ref * 181 + 255) >> 8 with 181 = 128 + 32 + 16 + 4 + 1 (ref * 2^-0.5), then shifted by k (rounded up when shifting right), saturated to 2^W - 1.
// Bit-exact with cross_modal.quantile_track and cross_modal.cue_thresholds.
`timescale 1ns/1ps
module cortex_quant #(parameter W = 21, parameter E0 = 9, parameter K = 7, parameter EMIN = 2, parameter CW = 20) (
    input  wire clk, rst, valid, input wire [W-1:0] x, input wire [4:0] n,
    output reg  [W-1:0] q, output reg [CW-1:0] cnt
);
    wire [CW-1:0] sh = cnt >> K;
    wire [4:0] e = (sh >= E0 - EMIN) ? EMIN : (E0 - sh);
    wire [W+5:0] up = ({{(W+1){1'b0}}, n}) << e, dn = ({{(W+1){1'b0}}, (5'd16 - n)}) << e;
    wire [W+6:0] qup = {1'b0, 1'b0, q} + {1'b0, up}; wire [W+6:0] qdn = {1'b0, 1'b0, q} - {1'b0, dn};
    always @(posedge clk) begin
        if (rst) begin q <= 0; cnt <= 0; end
        else if (valid) begin
            if (cnt == 0) q <= x;
            else if (x < q) q <= qdn[W+6] ? {W{1'b0}} : qdn[W-1:0];
            else q <= (qup > {{7{1'b0}}, {W{1'b1}}}) ? {W{1'b1}} : qup[W-1:0];
            if (cnt != {CW{1'b1}}) cnt <= cnt + 1;
        end
    end
endmodule

module cortex_cuethr #(parameter W = 21) (input wire [W-1:0] ref, output reg [7*W-1:0] t);
    reg [W+8:0] h, hk; integer k; reg [W+12:0] v; localparam [W+12:0] TOPV = {{13{1'b0}}, {W{1'b1}}};
    always @(*) begin
        h = ({ref, 7'b0} + {ref, 5'b0} + {ref, 4'b0} + {ref, 2'b0} + ref + 9'd255) >> 8;
        for (k = -3; k <= 3; k = k + 1) begin
            if (k < 0) begin hk = h >> (-k); v = hk + (((h & ((1 << (-k)) - 1)) != 0) ? 1 : 0); end
            else v = h << k;
            t[(k + 3) * W +: W] = (v > TOPV) ? {W{1'b1}} : v[W-1:0];
        end
    end
endmodule
