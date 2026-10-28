// L Deep core: the routed clause layer over L Cortex's code (28 Oct 2026, SIMULATED/verified against ldeep_golden.py).
// Stage 2 of the pipeline: for one routed image it adds the stage-2 table rows of the active code bits, evaluates the kept
// clauses (each an AND of literals, evaluated literal by literal with early exit) and adds the table row of every clause
// that fires, then takes the argmax (first maximum wins, as numpy argmax). Integer only: adds, compares, no multiplier.
// in_bits = L's code bits [0..NCODE-1] followed by the raw pixel bits (>85 then >170). Memories load from hex files at
// time zero (simulation); a board top would stream them in from SRAM or flash.
module ldeep_core #(parameter NB = 6176, NCODE = 4608, NCL = 2000, NLITS = 13497) (
    input clk, input rst, input start, input [NB-1:0] in_bits,
    output reg busy, output reg done, output reg [3:0] pred, output [199:0] scores_flat, output reg [31:0] cycles);
    reg [79:0] wcode [0:NCODE-1]; reg [79:0] wcl [0:NCL-1]; reg [23:0] hdr [0:NCL-1]; reg [13:0] lits [0:NLITS-1];
    initial begin $readmemh("deep_wcode.hex", wcode); $readmemh("deep_wcl.hex", wcl); $readmemh("deep_hdr.hex", hdr); $readmemh("deep_lits.hex", lits); end
    reg signed [19:0] acc [0:9]; reg [NB-1:0] bits;
    genvar g; generate for (g = 0; g < 10; g = g + 1) begin : pk assign scores_flat[20*g +: 20] = acc[g]; end endgenerate
    localparam S_IDLE = 0, S_CODE = 1, S_HDR = 2, S_LIT = 3, S_ARG = 4;
    reg [2:0] st; reg [12:0] i; reg [12:0] c; reg [7:0] t; reg [15:0] lstart; reg [7:0] lcnt; reg [3:0] k; reg signed [19:0] best; reg [3:0] bidx;
    reg [13:0] lit; reg bitv; reg [23:0] h; integer j;
    always @(posedge clk) begin
        if (rst) begin st <= S_IDLE; busy <= 0; done <= 0; pred <= 0; cycles <= 0; end
        else begin
            done <= 0;
            case (st)
                S_IDLE: if (start) begin bits <= in_bits; for (j = 0; j < 10; j = j + 1) acc[j] <= 0; i <= 0; c <= 0; cycles <= 0; busy <= 1; st <= S_CODE; end
                S_CODE: begin cycles <= cycles + 1;
                    if (i == NCODE) st <= S_HDR;
                    else begin if (bits[i]) for (j = 0; j < 10; j = j + 1) acc[j] <= acc[j] + $signed(wcode[i][8*j +: 8]); i <= i + 1; end end
                S_HDR: begin cycles <= cycles + 1;
                    if (c == NCL) begin k <= 1; best <= acc[0]; bidx <= 0; st <= S_ARG; end
                    else begin h = hdr[c]; lstart <= h[23:8]; lcnt <= h[7:0]; t <= 0; if (h[7:0] == 0) c <= c + 1; else st <= S_LIT; end end
                S_LIT: begin cycles <= cycles + 1; lit = lits[lstart + t];
                    bitv = (lit < NB) ? bits[lit] : ~bits[lit - NB];
                    if (!bitv) begin c <= c + 1; st <= S_HDR; end
                    else if (t + 1 == lcnt) begin for (j = 0; j < 10; j = j + 1) acc[j] <= acc[j] + $signed(wcl[c][8*j +: 8]); c <= c + 1; st <= S_HDR; end
                    else t <= t + 1; end
                S_ARG: begin cycles <= cycles + 1;
                    if (k == 10) begin pred <= bidx; done <= 1; busy <= 0; st <= S_IDLE; end
                    else begin if (acc[k] > best) begin best <= acc[k]; bidx <= k; end k <= k + 1; end end
            endcase
        end
    end
endmodule
