// L system top, two stages with a dispatcher (28 Oct 2026, SIMULATED/verified): stage 1 is L Cortex's table read (scan of the active code bits, adds of table rows),
// the dispatcher compares the margin (top score minus runner-up) with ROUTE_T and either answers at once or wakes L Deep (stage 2: code rows plus the kept clauses),
// whose answer replaces the first. Same integer pipeline as ldeep_golden.py. Block-RAM friendly (synchronous reads); input bits loaded through (wr_en, wr_addr, wr_bit).
module l_system #(parameter NB = 6176, NCODE = 4608, NCL = 4000, NLITS = 22232, ROUTE_T = 3415) (
    input clk, input rst, input wr_en, input [12:0] wr_addr, input wr_bit, input start,
    output reg busy, output reg done, output reg routed, output reg [3:0] pred, output [199:0] scores_flat, output reg [31:0] cycles, output s2_active);
    reg [79:0] wcode1 [0:NCODE-1]; reg [79:0] wcode [0:NCODE-1]; reg [79:0] wcl [0:NCL-1]; reg [23:0] hdr [0:NCL-1]; reg [13:0] lits [0:NLITS-1]; reg bitsm [0:NB-1];
    initial begin $readmemh("deep_wcode1.hex", wcode1); $readmemh("deep_wcode.hex", wcode); $readmemh("deep_wcl.hex", wcl); $readmemh("deep_hdr.hex", hdr); $readmemh("deep_lits.hex", lits); end
    reg signed [19:0] acc [0:9];
    genvar g; generate for (g = 0; g < 10; g = g + 1) begin : pk assign scores_flat[20*g +: 20] = acc[g]; end endgenerate
    localparam S_IDLE = 0, S_CODE = 1, S_H = 2, S_H2 = 3, S_L1 = 4, S_L2 = 5, S_L3 = 6, S_L4 = 7, S_F1 = 8, S_F2 = 9, S_ARG = 10, S_C1 = 11, S_M = 12;
    reg [3:0] st; reg stage2; reg [12:0] i; reg [12:0] c; reg [7:0] t; reg [14:0] la; reg [7:0] lcnt; reg [3:0] k; reg signed [19:0] best, second; reg [3:0] bidx; reg [12:0] ba; reg inv; integer j;
    assign s2_active = stage2 && busy;
    wire [12:0] bit_addr = (st == S_CODE || st == S_C1) ? i : ba;
    reg [79:0] wcode1_q, wcode_q, wcl_q; reg [23:0] hdr_q; reg [13:0] lits_q; reg bit_q;
    always @(posedge clk) begin
        wcode1_q <= wcode1[i]; wcode_q <= wcode[i]; wcl_q <= wcl[c]; hdr_q <= hdr[c]; lits_q <= lits[la]; bit_q <= bitsm[bit_addr];
        if (wr_en) bitsm[wr_addr] <= wr_bit;
    end
    wire [79:0] row = stage2 ? wcode_q : wcode1_q;
    task go_arg; begin k <= 1; best <= acc[0]; second <= -20'sd524288; bidx <= 0; st <= S_ARG; end endtask
    always @(posedge clk) begin
        if (rst) begin st <= S_IDLE; busy <= 0; done <= 0; pred <= 0; cycles <= 0; routed <= 0; stage2 <= 0; end
        else begin
            done <= 0; if (st != S_IDLE) cycles <= cycles + 1;
            case (st)
                S_IDLE: if (start) begin for (j = 0; j < 10; j = j + 1) acc[j] <= 0; i <= 0; c <= 0; cycles <= 0; busy <= 1; stage2 <= 0; routed <= 0; st <= S_CODE; end
                S_CODE: begin
                    if (i != 0 && bit_q) for (j = 0; j < 10; j = j + 1) acc[j] <= acc[j] + $signed(row[8*j +: 8]);
                    if (i == NCODE) begin if (stage2) begin st <= S_H; c <= 0; end else go_arg; end else i <= i + 1; end
                S_H: st <= S_H2;
                S_H2: begin lcnt <= hdr_q[7:0]; la <= hdr_q[23:8]; t <= 0; if (hdr_q[7:0] == 0) begin c <= c + 1; if (c + 1 == NCL) go_arg; else st <= S_H; end else st <= S_L1; end
                S_L1: st <= S_L2;
                S_L2: begin if (lits_q < NB) begin ba <= lits_q; inv <= 0; end else begin ba <= lits_q - NB; inv <= 1; end st <= S_L3; end
                S_L3: st <= S_L4;
                S_L4: begin
                    if (!(inv ? ~bit_q : bit_q)) begin c <= c + 1; if (c + 1 == NCL) go_arg; else st <= S_H; end
                    else if (t + 1 == lcnt) st <= S_F1;
                    else begin t <= t + 1; la <= la + 1; st <= S_L1; end end
                S_F1: st <= S_F2;
                S_F2: begin for (j = 0; j < 10; j = j + 1) acc[j] <= acc[j] + $signed(wcl_q[8*j +: 8]); c <= c + 1; if (c + 1 == NCL) go_arg; else st <= S_H; end
                S_ARG: begin
                    if (k == 10) begin
                        if (!stage2 && (best - second) <= ROUTE_T) begin for (j = 0; j < 10; j = j + 1) acc[j] <= 0; stage2 <= 1; routed <= 1; i <= 0; st <= S_CODE; end
                        else begin pred <= bidx; done <= 1; busy <= 0; st <= S_IDLE; end
                    end else begin
                        if (acc[k] > best) begin second <= best; best <= acc[k]; bidx <= k; end else if (acc[k] > second) second <= acc[k];
                        k <= k + 1; end end
            endcase
        end
    end
endmodule
