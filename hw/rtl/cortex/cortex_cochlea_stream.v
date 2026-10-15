// SPARK Cortex streaming cochlea: listens live. Each 16 kHz sample is taken as it arrives (smp_valid / smp_ready) and
// all 28 resonators are updated from it, one per cycle (28 cycles per sample, so a 0.5 MHz clock would keep up); no
// second of sound is stored. Per resonator only its two past outputs, its running frame sum and its 4 quietest frame
// sums are kept (~6 kbit in all, instead of the 256 kbit sample buffer of cortex_cochlea.v). Same arithmetic, same
// noise floor, same integer log picture: bit-exact with hw/brain/cochlea_int.py. Pulse start before the first sample
// of a clip; after 15,988 samples the picture comes out on px_we / px_addr / px_data and done pulses (further samples
// of the clip are ignored until the next start).
`timescale 1ns/1ps
module cortex_cochlea_stream #(parameter FB = 8) (
    input  wire        clk, rst,
    input  wire        start,
    input  wire        smp_valid, input wire [15:0] smp_data, output wire smp_ready,
    output reg         busy, output reg done,
    output reg         px_we, output reg [9:0] px_addr, output reg [7:0] px_data
);
    localparam FR = 28, FL = 571, NS = FL * FR;
    reg signed [47:0] y1m [0:27], y2m [0:27];
    reg [31:0] accm [0:27], m0m [0:27], m1m [0:27], m2m [0:27], m3m [0:27];
    reg [33:0] flr [0:27];
    reg [31:0] sums [0:783];
    reg [6:0]  lgm [0:783];
    reg [9:0] sa; reg [31:0] sq_sum; reg [6:0] lq;
    always @(posedge clk) begin sq_sum <= sums[sa]; lq <= lgm[sa]; end

`include "cochlea_coef.vh"
    function signed [47:0] shs; input signed [47:0] v; input [5:0] e; begin
        shs = e[5] ? (v >>> (~e + 1'b1)) : (v <<< e);
    end endfunction
    function [4:0] msb; input [31:0] v; integer q; begin
        msb = 0; for (q = 0; q < 32; q = q + 1) if (v[q]) msb = q;
    end endfunction

    localparam S_IDLE = 0, S_WAIT = 1, S_RES = 2, S_L0 = 3, S_L1 = 4, S_L2 = 5, S_P0 = 6, S_P1 = 7, S_P2 = 8;
    reg [3:0] st;
    reg [4:0] k; reg [13:0] n; reg [9:0] cnt; reg [4:0] fr;
    reg signed [47:0] xs, x1, x2;                     // current sample and the two before it (shared by all resonators)
    reg [9:0] i; reg [6:0] top; reg [4:0] kk, ff;
    assign smp_ready = (st == S_WAIT);
    wire [69:0] cf = coef(k);
    wire signed [47:0] yk1 = y1m[k], yk2 = y2m[k];
    reg signed [47:0] y, ya; integer t;
    always @(*) begin
        y = shs(xs - x2, cf[5:0] + FB);
        for (t = 0; t < 4; t = t + 1) begin
            if (cf[69 - 8*t -: 2] == 2'd1) y = y + shs(yk1, cf[67 - 8*t -: 6]);
            if (cf[69 - 8*t -: 2] == 2'd3) y = y - shs(yk1, cf[67 - 8*t -: 6]);
            if (cf[37 - 8*t -: 2] == 2'd1) y = y - shs(yk2, cf[35 - 8*t -: 6]);
            if (cf[37 - 8*t -: 2] == 2'd3) y = y + shs(yk2, cf[35 - 8*t -: 6]);
        end
        ya = (y < 0) ? -y : y;
    end
    wire frame_end = (cnt == FL - 1);
    wire [31:0] fsum = accm[k] + (ya >> FB);
    wire [31:0] mk0 = m0m[k], mk1 = m1m[k], mk2 = m2m[k], mk3 = m3m[k];
    wire [31:0] n0 = (fsum < mk0) ? fsum : mk0;
    wire [31:0] n1 = (fsum < mk0) ? mk0 : (fsum < mk1) ? fsum : mk1;
    wire [31:0] n2 = (fsum < mk1) ? mk1 : (fsum < mk2) ? fsum : mk2;
    wire [31:0] n3 = (fsum < mk2) ? mk2 : (fsum < mk3) ? fsum : mk3;
    wire [33:0] n4 = {2'b0, n0} + n1 + n2 + n3;
    wire [33:0] fl_k = flr[kk];
    wire [31:0] v1 = ({2'b0, sq_sum} > fl_k) ? sq_sum - fl_k[31:0] : 32'd1;
    wire [4:0]  e1 = msb(v1);
    wire [31:0] vs = v1 >> ((e1 >= 2) ? (e1 - 2) : 0);
    wire [6:0]  lg = {e1, 2'b00} + vs[1:0];
    wire [9:0]  dl = {top - lq, 3'b000};
    wire [7:0]  pxv = (dl > 255) ? 8'd0 : 8'd255 - dl[7:0];
    integer q;

    always @(posedge clk) begin
        done <= 0; px_we <= 0;
        if (rst) begin st <= S_IDLE; busy <= 0; end
        else case (st)
        S_IDLE: if (start) begin
            busy <= 1; n <= 0; cnt <= 0; fr <= 0; x1 <= 0; x2 <= 0; st <= S_WAIT;
            for (q = 0; q < 28; q = q + 1) begin
                y1m[q] <= 0; y2m[q] <= 0; accm[q] <= 0;
                m0m[q] <= 32'hffffffff; m1m[q] <= 32'hffffffff; m2m[q] <= 32'hffffffff; m3m[q] <= 32'hffffffff;
            end
        end
        S_WAIT: if (smp_valid) begin xs <= {{32{smp_data[15]}}, smp_data}; k <= 0; st <= S_RES; end
        // ---- one resonator per cycle for this sample --------------------------------------------------------------
        S_RES: begin
            y2m[k] <= yk1; y1m[k] <= y;
            if (frame_end) begin
                sums[k * FR + fr] <= fsum; accm[k] <= 0;
                m0m[k] <= n0; m1m[k] <= n1; m2m[k] <= n2; m3m[k] <= n3;
                if (fr == FR - 1) flr[k] <= {n4[33:2], 2'b00};
            end else accm[k] <= fsum;
            if (k == 27) begin
                x2 <= x1; x1 <= xs;
                if (frame_end) begin cnt <= 0; fr <= fr + 1'b1; end else cnt <= cnt + 1'b1;
                if (n == NS - 1) begin i <= 0; top <= 0; kk <= 0; ff <= 0; st <= S_L0; end
                else begin n <= n + 1'b1; st <= S_WAIT; end
            end else k <= k + 1'b1;
        end
        // ---- pass 1: integer log of every frame sum minus its floor, and the largest -------------------------------
        S_L0: begin sa <= i; st <= S_L1; end
        S_L1: st <= S_L2;
        S_L2: begin
            lgm[i] <= lg; if (lg > top) top <= lg;
            if (ff == FR - 1) begin ff <= 0; kk <= kk + 1'b1; end else ff <= ff + 1'b1;
            if (i == 783) begin i <= 0; st <= S_P0; end else begin i <= i + 1'b1; st <= S_L0; end
        end
        // ---- pass 2: pixels relative to the loudest frame ----------------------------------------------------------
        S_P0: begin sa <= i; st <= S_P1; end
        S_P1: st <= S_P2;
        S_P2: begin
            px_we <= 1; px_addr <= i; px_data <= pxv;
            if (i == 783) begin done <= 1; busy <= 0; st <= S_IDLE; end else begin i <= i + 1'b1; st <= S_P0; end
        end
        default: st <= S_IDLE;
        endcase
    end
endmodule
