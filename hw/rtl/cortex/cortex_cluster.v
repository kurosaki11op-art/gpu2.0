// SPARK Cortex clustering unit (22 Oct 2026): label-free grouping of the sleep-time buffer of unlabelled pairs, integers only, no multiplier and no divider. Bit-exact with cross_modal.kmeans_int.
//   buffer: NS pairs, each a list of up to LM active code-bit indices; prototypes: K groups, a level 0..4 (3 bits) per code bit and group (the member rate x 4, found by compares: level = #{l in 1..4 : 8 c >= (2 l - 1) m})
//   score of a pair for group j = sum of the group's levels over the pair's bits - (sum of squared levels of the group) >> 3; the group with the largest score wins (lowest j on a tie)
//   RST restarts: restart r starts from the pairs ini[r*K + i] (loaded by the host: stride positions in the buffer); ITER assign + update iterations, then a final assignment; the restart with the largest total score wins (first on a tie)
// host interface: write lists (lw_we, lw_pair, lw_pos, lw_val), lengths (ln_we, ln_pair, ln_val), init table (in_we, in_idx, in_val); pulse start; wait for done; read assignments with rd_pair -> rd_group (valid 1 cycle later), best total in tot_out.
`timescale 1ns/1ps
module cortex_cluster #(parameter NB = 256, AW = 8, NS = 48, PW = 6, LM = 40, K = 4, CW = 8, ITER = 3, RST = 2) (
    input  wire clk, rst,
    input  wire lw_we, input wire [PW-1:0] lw_pair, input wire [7:0] lw_pos, input wire [AW-1:0] lw_val,
    input  wire ln_we, input wire [PW-1:0] ln_pair, input wire [7:0] ln_val,
    input  wire in_we, input wire [7:0] in_idx, input wire [PW-1:0] in_val,
    input  wire start, output reg busy, output reg done,
    input  wire [PW-1:0] rd_pair, output reg [3:0] rd_group, output reg signed [31:0] tot_out
);
    reg [AW-1:0] lst [0:NS*LM-1]; reg [7:0] len [0:NS-1]; reg [PW-1:0] ini [0:RST*K-1];
    reg [K*3-1:0] Rm [0:NB-1]; reg [K*CW-1:0] Cm [0:NB-1];
    reg [3:0] asg [0:NS-1]; reg [3:0] basg [0:NS-1]; reg [CW-1:0] mcnt [0:K-1]; reg [31:0] pensq [0:K-1]; reg signed [31:0] acc [0:K-1];
    reg signed [31:0] tot, besttot; reg have;
    always @(posedge clk) begin
        if (lw_we) lst[lw_pair * LM + lw_pos] <= lw_val;
        if (ln_we) len[ln_pair] <= ln_val;
        if (in_we) ini[in_idx] <= in_val;
        rd_group <= basg[rd_pair];
    end
    localparam S_IDLE = 0, S_CLR = 1, S_SEED = 2, S_SEEDP = 3, S_A0 = 4, S_A1 = 5, S_A2 = 6, S_CMP = 7, S_COPY = 8, S_UC = 9, S_U0 = 10, S_U1 = 11, S_D0 = 12, S_D1 = 13, S_FIN = 14;
    reg [4:0] st; integer r, it, b, i, n, pos, j, sc_i, uj; reg [AW-1:0] bit_addr; reg signed [31:0] sc, bsc, sq; reg [3:0] arg; reg [K*3-1:0] w; reg [K*CW-1:0] cw; reg [2:0] lv; reg [CW+3:0] c8, t1, t3, t5, t7, mm;
    reg [4:0] sqv;
    function [4:0] sqf; input [2:0] v; begin case (v) 3'd0: sqf = 0; 3'd1: sqf = 1; 3'd2: sqf = 4; 3'd3: sqf = 9; default: sqf = 16; endcase end endfunction
    always @(posedge clk) begin
        if (rst) begin st <= S_IDLE; busy <= 0; done <= 0; end
        else case (st)
        S_IDLE: begin done <= 0; if (start) begin busy <= 1; r = 0; have = 0; b = 0; st <= S_CLR; end end
        // restart r: clear the prototypes, then seed the K prototypes from the K chosen pairs (level 4 on their bits)
        S_CLR: begin Rm[b] <= {(K*3){1'b0}}; if (b == NB - 1) begin i = 0; pos = 0; st <= S_SEED; end else b = b + 1; end
        S_SEED: begin
            if (i == K) begin it = 0; n = 0; for (j = 0; j < K; j = j + 1) acc[j] = 0; pos = 0; tot = 0; st <= S_A1; end
            else begin n = ini[r * K + i]; pensq[i] = 16 * len[n]; pos = 0; st <= S_SEEDP; end
        end
        S_SEEDP: begin
            if (pos == len[n]) begin i = i + 1; st <= S_SEED; end
            else begin bit_addr = lst[n * LM + pos]; w = Rm[bit_addr]; w[i*3 +: 3] = 3'd4; Rm[bit_addr] <= w; pos = pos + 1; end
        end
        // assignment pass: n = pair, pos = position in its list
        S_A0: begin for (j = 0; j < K; j = j + 1) acc[j] = 0; pos = 0; st <= S_A1; end
        S_A1: begin
            if (pos == len[n]) st <= S_A2;
            else begin bit_addr = lst[n * LM + pos]; w = Rm[bit_addr]; for (j = 0; j < K; j = j + 1) acc[j] = acc[j] + w[j*3 +: 3]; pos = pos + 1; end
        end
        S_A2: begin
            bsc = 0; arg = 0;
            for (j = 0; j < K; j = j + 1) begin sc = acc[j] - $signed(pensq[j] >> 3); if (j == 0 || sc > bsc) begin bsc = sc; arg = j; end end   // $signed: acc is signed, an unsigned shift would make the subtraction unsigned
            asg[n] <= arg; tot = tot + bsc;
            if (n == NS - 1) begin if (it == ITER) st <= S_CMP; else begin b = 0; st <= S_UC; end end
            else begin n = n + 1; st <= S_A0; end
        end
        // after the final assignment: keep the best restart
        S_CMP: begin
            if (!have || tot > besttot) begin besttot = tot; have = 1; n = 0; st <= S_COPY; end
            else begin r = r + 1; if (r == RST) st <= S_FIN; else begin b = 0; st <= S_CLR; end end
        end
        S_COPY: begin basg[n] <= asg[n]; if (n == NS - 1) begin r = r + 1; if (r == RST) st <= S_FIN; else begin b = 0; st <= S_CLR; end end else n = n + 1; end
        // update: count the on-bits of every group's members, then derive the levels
        S_UC: begin Cm[b] <= {(K*CW){1'b0}}; if (b == NB - 1) begin for (j = 0; j < K; j = j + 1) mcnt[j] = 0; n = 0; pos = 0; st <= S_U0; end else b = b + 1; end
        S_U0: begin
            if (n == NS) begin b = 0; for (j = 0; j < K; j = j + 1) pensq[j] = 0; st <= S_D0; end
            else begin if (pos == 0) mcnt[asg[n]] = mcnt[asg[n]] + 1; if (pos == len[n]) begin n = n + 1; pos = 0; end else begin bit_addr = lst[n * LM + pos]; cw = Cm[bit_addr]; uj = asg[n]; cw[uj*CW +: CW] = cw[uj*CW +: CW] + 1; Cm[bit_addr] <= cw; pos = pos + 1; end end
        end
        S_D0: begin
            w = Rm[b]; cw = Cm[b];
            for (j = 0; j < K; j = j + 1) begin
                lv = w[j*3 +: 3];
                if (mcnt[j] != 0) begin
                    mm = {{4{1'b0}}, mcnt[j]}; c8 = {cw[j*CW +: CW], 3'b0}; t1 = mm; t3 = (mm << 1) + mm; t5 = (mm << 2) + mm; t7 = (mm << 3) - mm;
                    lv = (c8 >= t1) + (c8 >= t3) + (c8 >= t5) + (c8 >= t7);
                end
                w[j*3 +: 3] = lv; sqv = sqf(lv); pensq[j] = pensq[j] + sqv;
            end
            Rm[b] <= w; if (b == NB - 1) begin it = it + 1; n = 0; tot = 0; st <= S_A0; end else b = b + 1;
        end
        S_FIN: begin tot_out <= besttot; busy <= 0; done <= 1; st <= S_IDLE; end
        default: st <= S_IDLE;
        endcase
    end
endmodule
