// SPARK Cortex second-look unit (21 Oct 2026): table A (coarse code) answers when it is sure; when its top-2 score margin is below a host-loaded threshold TH, the fine-code table B is consulted
// and the two score vectors are added. pred = first known class with the top (A) or (A + B) score. Compares and adds only. Bit-exact with cross_modal.look_combine.
//   the host sets TH = a percentile of A's margins on UNLABELLED data (the share of inputs that get a second look, e.g. 20-40 %)
`timescale 1ns/1ps
module cortex_look #(parameter C = 10, parameter SW = 20) (
    input  wire [C*SW-1:0] sa, sb,
    input  wire [C-1:0]    known,
    input  wire [SW:0]     th,
    output reg  [3:0]      pred,
    output reg             look
);
    localparam MW = SW + 1;
    reg signed [SW:0] best, comb; reg signed [SW-1:0] top, snd, v; reg h1, h2, have; integer j, nkn; reg [MW-1:0] m;
    always @(*) begin
        nkn = 0; top = 0; snd = 0; h1 = 0; h2 = 0;
        for (j = 0; j < C; j = j + 1) if (known[j]) begin
            v = sa[j*SW +: SW]; nkn = nkn + 1;
            if (!h1 || v > top) begin if (h1) begin snd = top; h2 = 1; end top = v; h1 = 1; end
            else if (!h2 || v > snd) begin snd = v; h2 = 1; end
        end
        if (nkn == 0) m = 0; else if (nkn == 1) m = {MW{1'b1}}; else m = top - snd;   // explicit branches: a ?: with an unsigned constant would zero-extend the signed difference
        look = (m < th);
        have = 0; best = 0; pred = 0;
        for (j = 0; j < C; j = j + 1) if (known[j]) begin
            comb = $signed(sa[j*SW +: SW]); if (look) comb = comb + $signed(sb[j*SW +: SW]);
            if (!have || comb > best) begin best = comb; pred = j; have = 1; end
        end
    end
endmodule
