// SPARK Cortex cue-weighting unit (21 Oct 2026): combines the class scores of two senses, each weighted by how confident it is right now
// (reliability-weighted cue combination). Shifts, adds and compares only: no multiplier, no divider.
//   margin   = top score minus runner-up among the known classes (one known class: saturated; none: 0), per sense
//   index    = number of the 7 host-loaded thresholds (ascending, T = typical clean margin * 2^(k-0.5), k = -3..3) that the margin reaches (0..7 = exponent + 4)
//   combined = (score_a << (ia - min(ia, ib))) + (score_b << (ib - min(ia, ib)));  pred = first known class with the top combined score
// Bit-exact with cross_modal.cue_combine. Purely combinational (the host reads the answer the cycle after loading the scores).
`timescale 1ns/1ps
module cortex_cue #(parameter C = 10, parameter SW = 20) (
    input  wire [C*SW-1:0] sa, sb,                 // class scores of sense A and B (signed fields)
    input  wire [C-1:0]    known,
    input  wire [7*(SW+1)-1:0] ta, tb,             // 7 ascending thresholds per sense (unsigned, SW+1 bits)
    output reg  [3:0]      pred,
    output reg  [2:0]      ia_o, ib_o             // the two confidence indices (for the host / checks)
);
    localparam MW = SW + 1;
    localparam CW = SW + 9;
    reg signed [SW-1:0] va, vb; reg signed [CW-1:0] best, comb, ca, cb;
    reg [MW-1:0] ma, mb; reg signed [SW-1:0] t1, t2; reg [3:0] nk; integer j, k, sh_a, sh_b, ia, ib, i0; reg have;
    function [MW-1:0] margin; input [C*SW-1:0] s; input [C-1:0] kn; integer q, nkn; reg signed [SW-1:0] top, snd, v; reg h1, h2; begin
        nkn = 0; top = 0; snd = 0; h1 = 0; h2 = 0;
        for (q = 0; q < C; q = q + 1) if (kn[q]) begin
            v = s[q*SW +: SW]; nkn = nkn + 1;
            if (!h1 || v > top) begin if (h1) begin snd = top; h2 = 1; end top = v; h1 = 1; end
            else if (!h2 || v > snd) begin snd = v; h2 = 1; end
        end
        if (nkn == 0) margin = 0; else if (nkn == 1) margin = {MW{1'b1}}; else margin = top - snd;
    end endfunction
    function [2:0] idx; input [MW-1:0] m; input [7*MW-1:0] t; integer q; begin
        idx = 0; for (q = 0; q < 7; q = q + 1) if (m >= t[q*MW +: MW]) idx = idx + 1;
    end endfunction
    always @(*) begin
        ma = margin(sa, known); mb = margin(sb, known); ia = idx(ma, ta); ib = idx(mb, tb); i0 = (ia < ib) ? ia : ib; sh_a = ia - i0; sh_b = ib - i0;
        ia_o = ia; ib_o = ib; have = 0; best = 0; pred = 0;
        for (j = 0; j < C; j = j + 1) if (known[j]) begin
            va = sa[j*SW +: SW]; vb = sb[j*SW +: SW]; ca = va; cb = vb; ca = ca <<< sh_a; cb = cb <<< sh_b; comb = ca + cb;
            if (!have || comb > best) begin best = comb; pred = j; have = 1; end
        end
    end
endmodule
