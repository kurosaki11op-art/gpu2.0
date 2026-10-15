// SPARK Cortex cochlea: 1 s of 16 kHz sound (16,000 signed 16-bit samples) -> 28x28 sound picture (784 bytes),
// bit-exact with hw/brain/cochlea_int.py (sound_picture_int). 28 resonators (basilar-membrane places) run one after
// another; each sample step is y = g (x[n] - x[n-2]) + a1 y[n-1] - a2 y[n-2] with a1, a2 given as up to 4 signed
// powers of two each and g a power of two (cochlea_coef.vh), so the whole step is shifts and adds - no multiplier.
// Each 1/28 s frame sums |y| >> FB. Noise floor (auditory adaptation): each resonator keeps its 4 quietest frame
// sums (4 compares per frame); its floor is their sum with the 2 low bits cleared, subtracted from every frame sum
// (at least 1). The picture is an integer log of those values (leading-one position + the next two bits), relative
// to the loudest one: px = clip(255 - 8 (top - lg)).
// Load samples with smp_we, pulse start; pixels come out on px_we / px_addr / px_data (index = resonator*28 + frame);
// done pulses at the end. ~3 cycles per sample per resonator (~1.35 M cycles per second of sound).
`timescale 1ns/1ps
module cortex_cochlea #(parameter FB = 8) (
    input  wire        clk, rst,
    input  wire        smp_we, input wire [13:0] smp_addr, input wire [15:0] smp_data,
    input  wire        start,
    output reg         busy, output reg done,
    output reg         px_we, output reg [9:0] px_addr, output reg [7:0] px_data
);
    localparam FR = 28, FL = 571, NS = FL * FR;            // frames, samples per frame, samples used (15,988)
    reg [15:0] smp [0:15999];
    reg [31:0] sums [0:783];
    reg [6:0]  lgm [0:783];
    reg [33:0] flr [0:27];                                  // per-resonator noise floor
    reg [31:0] m0, m1, m2, m3;                              // the 4 quietest frame sums so far (m0 smallest)
    always @(posedge clk) if (smp_we) smp[smp_addr] <= smp_data;
    reg [13:0] ra; reg signed [15:0] sq;
    always @(posedge clk) sq <= smp[ra];
    reg [9:0] sa; reg [31:0] sq_sum; reg [6:0] lq;
    always @(posedge clk) begin sq_sum <= sums[sa]; lq <= lgm[sa]; end

`include "cochlea_coef.vh"
    function signed [47:0] shs; input signed [47:0] v; input [5:0] e; begin
        shs = e[5] ? (v >>> (~e + 1'b1)) : (v <<< e);
    end endfunction
    function [4:0] msb; input [31:0] v; integer q; begin
        msb = 0; for (q = 0; q < 32; q = q + 1) if (v[q]) msb = q;
    end endfunction

    localparam S_IDLE = 0, S_RD = 1, S_WT = 2, S_CMP = 3, S_L0 = 4, S_L1 = 5, S_L2 = 6, S_P0 = 7, S_P1 = 8, S_P2 = 9;
    reg [3:0] st;
    reg [4:0] k; reg [13:0] n; reg [9:0] cnt; reg [4:0] fr; reg [31:0] acc;
    reg signed [47:0] y1, y2, x1, x2; reg [9:0] i; reg [6:0] top; reg [4:0] kk, ff;
    wire [69:0] cf = coef(k);
    // one resonator step (combinational)
    reg signed [47:0] y, ya; integer t;
    always @(*) begin
        y = shs({{32{sq[15]}}, sq} - x2, cf[5:0] + FB);
        for (t = 0; t < 4; t = t + 1) begin
            if (cf[69 - 8*t -: 2] == 2'd1) y = y + shs(y1, cf[67 - 8*t -: 6]);
            if (cf[69 - 8*t -: 2] == 2'd3) y = y - shs(y1, cf[67 - 8*t -: 6]);
            if (cf[37 - 8*t -: 2] == 2'd1) y = y - shs(y2, cf[35 - 8*t -: 6]);
            if (cf[37 - 8*t -: 2] == 2'd3) y = y + shs(y2, cf[35 - 8*t -: 6]);
        end
        ya = (y < 0) ? -y : y;
    end
    wire [31:0] fsum = acc + (ya >> FB);                   // the frame sum completed in this cycle
    // the 4 quietest frame sums once fsum is inserted, and their sum with the low 2 bits cleared (= 4 x their mean)
    wire [31:0] n0 = (fsum < m0) ? fsum : m0;
    wire [31:0] n1 = (fsum < m0) ? m0 : (fsum < m1) ? fsum : m1;
    wire [31:0] n2 = (fsum < m1) ? m1 : (fsum < m2) ? fsum : m2;
    wire [31:0] n3 = (fsum < m2) ? m2 : (fsum < m3) ? fsum : m3;
    wire [33:0] n4 = {2'b0, n0} + n1 + n2 + n3;
    // integer log of a frame sum minus its resonator's floor (at least 1)
    wire [33:0] fl_k = flr[kk];
    wire [31:0] v1 = ({2'b0, sq_sum} > fl_k) ? sq_sum - fl_k[31:0] : 32'd1;
    wire [4:0]  e1 = msb(v1);
    wire [31:0] vs = v1 >> ((e1 >= 2) ? (e1 - 2) : 0);
    wire [6:0]  lg = {e1, 2'b00} + vs[1:0];
    wire [9:0]  dl = {top - lq, 3'b000};
    wire [7:0]  pxv = (dl > 255) ? 8'd0 : 8'd255 - dl[7:0];

    always @(posedge clk) begin
        done <= 0; px_we <= 0;
        if (rst) begin st <= S_IDLE; busy <= 0; end
        else case (st)
        S_IDLE: if (start) begin busy <= 1; k <= 0; n <= 0; cnt <= 0; fr <= 0; acc <= 0;
                                 y1 <= 0; y2 <= 0; x1 <= 0; x2 <= 0; st <= S_RD;
                                 m0 <= 32'hffffffff; m1 <= 32'hffffffff; m2 <= 32'hffffffff; m3 <= 32'hffffffff; end
        // ---- resonators ------------------------------------------------------------------------------------------
        S_RD: begin ra <= n; st <= S_WT; end
        S_WT: st <= S_CMP;
        S_CMP: begin
            y2 <= y1; y1 <= y; x2 <= x1; x1 <= {{32{sq[15]}}, sq};
            if (cnt == FL - 1) begin
                sums[k * FR + fr] <= fsum; acc <= 0; cnt <= 0; fr <= fr + 1'b1;
                m0 <= n0; m1 <= n1; m2 <= n2; m3 <= n3;
            end else begin acc <= acc + (ya >> FB); cnt <= cnt + 1'b1; end
            if (n == NS - 1) begin
                // the last frame of this resonator ends in this cycle (NS = FL x FR): fold it into the floor here
                flr[k] <= {n4[33:2], 2'b00};
                n <= 0; fr <= 0; y1 <= 0; y2 <= 0; x1 <= 0; x2 <= 0;
                m0 <= 32'hffffffff; m1 <= 32'hffffffff; m2 <= 32'hffffffff; m3 <= 32'hffffffff;
                if (k == 27) begin i <= 0; top <= 0; kk <= 0; ff <= 0; st <= S_L0; end
                else begin k <= k + 1'b1; st <= S_RD; end
            end else begin n <= n + 1'b1; st <= S_RD; end
        end
        // ---- pass 1: integer log of every frame sum, and the largest --------------------------------------------
        S_L0: begin sa <= i; st <= S_L1; end
        S_L1: st <= S_L2;
        S_L2: begin
            lgm[i] <= lg; if (lg > top) top <= lg;
            if (ff == FR - 1) begin ff <= 0; kk <= kk + 1'b1; end else ff <= ff + 1'b1;
            if (i == 783) begin i <= 0; st <= S_P0; end else begin i <= i + 1'b1; st <= S_L0; end
        end
        // ---- pass 2: pixels relative to the loudest frame ---------------------------------------------------------
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
