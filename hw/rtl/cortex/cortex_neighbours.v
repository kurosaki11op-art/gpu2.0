// SPARK Cortex sleep neighbours (20 Oct 2026): a buffer of NS codes (each a list of active code bits in increasing order, up to LW entries) and, for a query slot, the K buffered codes that share the most active bits with it
// (the overlap = popcount of the AND of the two codes = the number of common list entries, found by a two-pointer merge: compares and one counter, no multiplier). Ties: the lower slot wins (stable). Empty slots (length 0) and the query itself are skipped.
// Use (sleep cleaning, host side): write codes into slots (nw_we / nw_slot / nw_addr / nw_data, then len_we / len_slot / len_val), pulse start with qslot, wait for done, read nb_id (K slot numbers, best first) and nb_ov (their overlaps).
// The host pools the class scores (rd_scores of the core after a PREDICT per buffered code) of the K neighbours with the query's own and takes the winner as the new name: cross_modal.clean_names.
`timescale 1ns/1ps
module cortex_neighbours #(parameter NS = 64, parameter SW = 6, parameter LW = 10, parameter IW = 14, parameter K = 8) (
    input  wire          clk, rst,
    input  wire          nw_we, input wire [SW-1:0] nw_slot, input wire [LW-1:0] nw_addr, input wire [IW-1:0] nw_data,
    input  wire          len_we, input wire [SW-1:0] len_slot, input wire [LW:0] len_val,
    input  wire          start, input wire [SW-1:0] qslot,
    output reg           busy, output reg done,
    output wire [K*SW-1:0] nb_id, output wire [K*(LW+1)-1:0] nb_ov
);
    reg [IW-1:0] mem [0:NS*(1<<LW)-1]; reg [LW:0] len [0:NS-1];
    reg [LW:0] ovk [0:K-1]; reg [SW-1:0] idk [0:K-1]; reg okk [0:K-1];
    genvar g; generate for (g = 0; g < K; g = g + 1) begin : g_out
        assign nb_id[g*SW +: SW] = idk[g]; assign nb_ov[g*(LW+1) +: (LW+1)] = ovk[g];
    end endgenerate
    always @(posedge clk) begin
        if (nw_we) mem[{nw_slot, nw_addr}] <= nw_data;
        if (len_we) len[len_slot] <= len_val;
    end
    localparam S_IDLE = 0, S_NEXT = 1, S_MERGE = 2, S_INS = 3, S_DONE = 4;
    reg [2:0] st; reg [SW-1:0] q, t; reg [LW:0] i, j, cnt; integer k, p; reg found;
    wire [LW:0] la = len[q], lb = len[t];
    wire [IW-1:0] av = mem[{q, i[LW-1:0]}], bv = mem[{t, j[LW-1:0]}];
    reg [LW:0] n_ov [0:K-1]; reg [SW-1:0] n_id [0:K-1]; reg n_ok [0:K-1];
    reg last;
    always @(posedge clk) begin
        done <= 1'b0;
        if (rst) begin st <= S_IDLE; busy <= 1'b0; for (k = 0; k < K; k = k + 1) begin ovk[k] <= 0; idk[k] <= 0; okk[k] <= 1'b0; end end
        else case (st)
            S_IDLE: if (start) begin
                busy <= 1'b1; q <= qslot; t <= 0; for (k = 0; k < K; k = k + 1) begin ovk[k] <= 0; idk[k] <= 0; okk[k] <= 1'b0; end st <= S_NEXT;
            end
            S_NEXT: begin                                                  // next slot to compare with the query (skip the query and empty slots)
                if (t == NS - 1 && (t == q || len[t] == 0)) st <= S_DONE;
                else if (t == q || len[t] == 0) t <= t + 1'b1;
                else begin i <= 0; j <= 0; cnt <= 0; st <= S_MERGE; end
            end
            S_MERGE: begin
                if (i == la || j == lb) st <= S_INS;
                else if (av == bv) begin cnt <= cnt + 1'b1; i <= i + 1'b1; j <= j + 1'b1; end
                else if (av < bv) i <= i + 1'b1;
                else j <= j + 1'b1;
            end
            S_INS: begin                                                   // insert (cnt, t) after the entries with an overlap >= cnt (ties: the earlier slot stays first)
                p = K;
                for (k = K - 1; k >= 0; k = k - 1) if (!okk[k] || cnt > ovk[k]) p = k;
                for (k = 0; k < K; k = k + 1) begin
                    if (k < p) begin n_ov[k] = ovk[k]; n_id[k] = idk[k]; n_ok[k] = okk[k]; end
                    else if (k == p) begin n_ov[k] = cnt; n_id[k] = t; n_ok[k] = 1'b1; end
                    else begin n_ov[k] = ovk[k-1]; n_id[k] = idk[k-1]; n_ok[k] = okk[k-1]; end
                end
                for (k = 0; k < K; k = k + 1) begin ovk[k] <= n_ov[k]; idk[k] <= n_id[k]; okk[k] <= n_ok[k]; end
                if (t == NS - 1) st <= S_DONE; else begin t <= t + 1'b1; st <= S_NEXT; end
            end
            S_DONE: begin busy <= 1'b0; done <= 1'b1; st <= S_IDLE; end
            default: st <= S_IDLE;
        endcase
    end
endmodule
