// SPARK Cortex sleep pooling (20 Oct 2026): the last step of sleep cleaning, in hardware. For every buffered picture q: new name = the known class with the highest pooled score, pooled[c] = score[q][c] + sum over its K neighbours k of score[nb[q][k]][c] (+ EV * (K + 1) for the class the ear named); unknown classes are never chosen; the first class wins a tie.
// Integer adds and one compare per class: no multiplier (the vote is a constant added once; EV * (K + 1) is computed at elaboration). Inputs are the core's class scores (rd_scores after one PREDICT per buffered picture) and the neighbour unit's slot numbers (cortex_neighbours.v).
// Use: write scores (sc_we, sc_slot, sc_class, sc_val), neighbours (nbw_we, nbw_slot, nbw_k, nbw_id) and the ear's names (nm_we, nm_slot, nm_val); set known (one bit per class); pulse start; wait for done; read the new names with rd_slot / rd_name.
// Cycles: NS * C * (K + 2). Bit-exact with cross_modal.pool_names.
`timescale 1ns/1ps
module cortex_pool #(parameter NS = 64, parameter SW = 6, parameter C = 10, parameter K = 8, parameter VW = 20, parameter EV = 200) (
    input  wire          clk, rst,
    input  wire          sc_we, input wire [SW-1:0] sc_slot, input wire [3:0] sc_class, input wire signed [VW-1:0] sc_val,
    input  wire          nbw_we, input wire [SW-1:0] nbw_slot, input wire [3:0] nbw_k, input wire [SW-1:0] nbw_id,
    input  wire          nm_we, input wire [SW-1:0] nm_slot, input wire [3:0] nm_val,
    input  wire [C-1:0]  known, input wire [SW:0] nslots,
    input  wire          start, output reg busy, output reg done,
    input  wire [SW-1:0] rd_slot, output wire [3:0] rd_name
);
    localparam AWID = VW + 5 + 10;                                    // room for 9 scores plus the vote
    reg signed [VW-1:0] sc [0:NS*C-1]; reg [SW-1:0] nb [0:NS*K-1]; reg [3:0] nm [0:NS-1]; reg [3:0] res [0:NS-1];
    assign rd_name = res[rd_slot];
    always @(posedge clk) begin
        if (sc_we) sc[sc_slot * C + sc_class] <= sc_val;
        if (nbw_we) nb[nbw_slot * K + nbw_k] <= nbw_id;
        if (nm_we) nm[nm_slot] <= nm_val;
    end
    localparam S_IDLE = 0, S_OWN = 1, S_NB = 2, S_CMP = 3, S_DONE = 4;
    reg [2:0] st; reg [SW:0] q; reg [3:0] c, kk; reg signed [AWID-1:0] acc, best; reg [3:0] bestc; reg have;
    wire signed [AWID-1:0] vote = EV * (K + 1);
    wire [SW-1:0] nbq = nb[q[SW-1:0] * K + kk];
    always @(posedge clk) begin
        done <= 1'b0;
        if (rst) begin st <= S_IDLE; busy <= 1'b0; end
        else case (st)
            S_IDLE: if (start) begin busy <= 1'b1; q <= 0; c <= 0; have <= 1'b0; bestc <= 0; best <= 0; st <= S_OWN; end
            S_OWN: begin                                              // own score of class c (an unknown class counts 0 in the sums and is skipped when comparing)
                if (known[c]) acc <= sc[q[SW-1:0] * C + c]; else acc <= 0;                          // (explicit branches: a ?: mixing a signed value with an unsigned constant would zero-extend the score)
                kk <= 0; st <= S_NB;
            end
            S_NB: begin
                if (kk == K) st <= S_CMP;
                else begin if (known[c]) acc <= acc + sc[nbq * C + c]; kk <= kk + 1'b1; end
            end
            S_CMP: begin
                if (known[c]) begin
                    if (nm[q[SW-1:0]] == c) begin
                        if (!have || (acc + vote) > best) begin best <= acc + vote; bestc <= c; have <= 1'b1; end
                    end else if (!have || acc > best) begin best <= acc; bestc <= c; have <= 1'b1; end
                end
                if (c == C - 1) begin res[q[SW-1:0]] <= (known[c] && (nm[q[SW-1:0]] == c ? (!have || (acc + vote) > best) : (!have || acc > best))) ? c : bestc; c <= 0; have <= 1'b0; bestc <= 0; best <= 0;
                    if (q == nslots - 1) st <= S_DONE; else begin q <= q + 1'b1; st <= S_OWN; end end
                else begin c <= c + 1'b1; st <= S_OWN; end
            end
            S_DONE: begin busy <= 1'b0; done <= 1'b1; st <= S_IDLE; end
            default: st <= S_IDLE;
        endcase
    end
endmodule
