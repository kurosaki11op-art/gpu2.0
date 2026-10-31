// tile_mm: INT8 matrix engine of one tile (milestone M3, 31 Oct 2026). Plan and bars: hw/gpu/M3_plan.md.
// For m activation rows, reduction length k and nb blocks of LANES output columns: for every (row, block) it streams k steps; at each step it reads one word of LANES int8 weights and one int8 activation,
// multiplies the broadcast activation by the LANES weights, accumulates in LANES 32-bit accumulators, and emits the accumulator vector with its (row, block) index after the last step.
// The weight memory (w_addr -> w_data, word = LANES int8, lane l at bits 8l+7:8l) and the activation memory (a_addr -> a_data, one int8) are outside this module, one cycle of read latency each.
// Word address of weights = block * k + step (no multiplier: a running base); activation address = row * k + step (running base).
// Pipeline: cycle t issues the addresses; t+1 memory data arrives and the products are registered; t+2 accumulate; t+3 the result is visible with out_valid. Total cycles = m * nb * k + 3 after start.
module tile_mm #(parameter LANES = 64, parameter AW = 20, parameter CW = 12) (
    input clk, input rst, input start, input [CW-1:0] k, input [CW-1:0] m, input [CW-1:0] nb,
    output reg [AW-1:0] w_addr, input [8*LANES-1:0] w_data, output reg [AW-1:0] a_addr, input [7:0] a_data,
    output reg out_valid, output reg [32*LANES-1:0] out_acc, output reg [CW-1:0] out_row, output reg [CW-1:0] out_blk, output reg out_last, output reg busy);
    reg [CW-1:0] kq, mq, nbq, ks, bs, rs; reg [AW-1:0] wb, ab;
    reg v0, first0, last0, lastrun0; reg [CW-1:0] r0, b0;
    reg v1, first1, last1, lastrun1; reg [CW-1:0] r1, b1;
    reg v2, first2, last2, lastrun2; reg [CW-1:0] r2, b2;
    reg signed [15:0] prod [0:LANES-1]; reg signed [31:0] acc [0:LANES-1];
    integer i; genvar l;
    // address generation (cycle t)
    always @(posedge clk) begin
        if (rst) begin busy <= 0; v0 <= 0; end
        else begin
            v0 <= 0;
            if (start && !busy) begin busy <= 1; kq <= k; mq <= m; nbq <= nb; ks <= 0; bs <= 0; rs <= 0; wb <= 0; ab <= 0; end
            else if (busy) begin
                w_addr <= wb + ks; a_addr <= ab + ks; v0 <= 1; first0 <= (ks == 0); last0 <= (ks == kq - 1); r0 <= rs; b0 <= bs;
                lastrun0 <= (ks == kq - 1) && (bs == nbq - 1) && (rs == mq - 1);
                if (ks == kq - 1) begin
                    ks <= 0;
                    if (bs == nbq - 1) begin bs <= 0; wb <= 0; ab <= ab + kq; rs <= rs + 1; if (rs == mq - 1) busy <= 0; end
                    else begin bs <= bs + 1; wb <= wb + kq; end
                end else ks <= ks + 1;
            end
        end
    end
    // stage 1: memory data arrives, products registered
    generate for (l = 0; l < LANES; l = l + 1) begin : lane
        wire signed [7:0] wv = w_data[8*l +: 8]; wire signed [7:0] av = a_data;
        always @(posedge clk) prod[l] <= wv * av;
    end endgenerate
    always @(posedge clk) begin
        v1 <= v0; first1 <= first0; last1 <= last0; lastrun1 <= lastrun0; r1 <= r0; b1 <= b0;
        v2 <= v1; first2 <= first1; last2 <= last1; lastrun2 <= lastrun1; r2 <= r1; b2 <= b1;
    end
    // stage 2: accumulate; the result register is loaded at the last step
    generate for (l = 0; l < LANES; l = l + 1) begin : accl
        wire signed [31:0] nxt = (first2 ? 32'sd0 : acc[l]) + prod[l];
        always @(posedge clk) begin
            if (v2) acc[l] <= nxt;
            if (v2 && last2) out_acc[32*l +: 32] <= nxt;
        end
    end endgenerate
    always @(posedge clk) begin
        if (rst) begin out_valid <= 0; out_last <= 0; end
        else begin out_valid <= v2 && last2; out_last <= v2 && last2 && lastrun2; if (v2 && last2) begin out_row <= r2; out_blk <= b2; end end
    end
endmodule
