// L Deep core with P parallel engines (28 Oct 2026): each engine owns a slice of the code rows and an interleaved set of clauses (files deep_*_e<k>.hex from
// partition_engines.py), its own copy of the input-bit memory and its own 10 accumulators; engines run independently and the top adds the P partial score vectors,
// then takes the argmax (first maximum wins). Same function as ldeep_core.v, so the same expected scores apply (integer addition is order-independent).
module ldeep_eng #(parameter NB = 6176, NCODE_E = 1152, CODE_BASE = 0, NCL_E = 500, NLITS_E = 8192,
                   parameter F_WCODE = "deep_wcode_e0.hex", parameter F_WCL = "deep_wcl_e0.hex", parameter F_HDR = "deep_hdr_e0.hex", parameter F_LITS = "deep_lits_e0.hex") (
    input clk, input rst, input wr_en, input [12:0] wr_addr, input wr_bit, input start, output reg done, output [199:0] acc_flat);
    reg [79:0] wcode [0:NCODE_E-1]; reg [79:0] wcl [0:NCL_E-1]; reg [23:0] hdr [0:NCL_E-1]; reg [13:0] lits [0:NLITS_E-1]; reg bitsm [0:NB-1];
    initial begin $readmemh(F_WCODE, wcode); $readmemh(F_WCL, wcl); $readmemh(F_HDR, hdr); $readmemh(F_LITS, lits); end
    reg signed [19:0] acc [0:9]; genvar g; generate for (g = 0; g < 10; g = g + 1) begin : pk assign acc_flat[20*g +: 20] = acc[g]; end endgenerate
    localparam S_IDLE = 0, S_CODE = 1, S_H = 2, S_H2 = 3, S_L1 = 4, S_L2 = 5, S_L3 = 6, S_L4 = 7, S_F1 = 8, S_F2 = 9, S_DONE = 10;
    reg [3:0] st; reg [12:0] i; reg [12:0] c; reg [7:0] t; reg [14:0] la; reg [7:0] lcnt; reg [12:0] ba; reg inv; integer j;
    wire [12:0] bit_addr = (st == S_CODE) ? (CODE_BASE + i) : ba;
    reg [79:0] wcode_q, wcl_q; reg [23:0] hdr_q; reg [13:0] lits_q; reg bit_q;
    always @(posedge clk) begin wcode_q <= wcode[i]; wcl_q <= wcl[c]; hdr_q <= hdr[c]; lits_q <= lits[la]; bit_q <= bitsm[bit_addr]; if (wr_en) bitsm[wr_addr] <= wr_bit; end
    always @(posedge clk) begin
        if (rst) begin st <= S_IDLE; done <= 0; end
        else case (st)
            S_IDLE: begin done <= 0; if (start) begin for (j = 0; j < 10; j = j + 1) acc[j] <= 0; i <= 0; c <= 0; st <= S_CODE; end end
            S_CODE: begin
                if (i != 0 && bit_q) for (j = 0; j < 10; j = j + 1) acc[j] <= acc[j] + $signed(wcode_q[8*j +: 8]);
                if (i == NCODE_E) begin st <= S_H; c <= 0; end else i <= i + 1; end
            S_H: st <= S_H2;
            S_H2: begin lcnt <= hdr_q[7:0]; la <= hdr_q[23:8]; t <= 0; if (hdr_q[7:0] == 0) begin c <= c + 1; st <= (c + 1 == NCL_E) ? S_DONE : S_H; end else st <= S_L1; end
            S_L1: st <= S_L2;
            S_L2: begin if (lits_q < NB) begin ba <= lits_q; inv <= 0; end else begin ba <= lits_q - NB; inv <= 1; end st <= S_L3; end
            S_L3: st <= S_L4;
            S_L4: begin
                if (!(inv ? ~bit_q : bit_q)) begin c <= c + 1; st <= (c + 1 == NCL_E) ? S_DONE : S_H; end
                else if (t + 1 == lcnt) st <= S_F1;
                else begin t <= t + 1; la <= la + 1; st <= S_L1; end end
            S_F1: st <= S_F2;
            S_F2: begin for (j = 0; j < 10; j = j + 1) acc[j] <= acc[j] + $signed(wcl_q[8*j +: 8]); c <= c + 1; st <= (c + 1 == NCL_E) ? S_DONE : S_H; end
            S_DONE: begin done <= 1; if (start) begin done <= 0; for (j = 0; j < 10; j = j + 1) acc[j] <= 0; i <= 0; c <= 0; st <= S_CODE; end end
        endcase
    end
endmodule
module ldeep_core_p #(parameter NB = 6176) (
    input clk, input rst, input wr_en, input [12:0] wr_addr, input wr_bit, input start,
    output reg busy, output reg done, output reg [3:0] pred, output [199:0] scores_flat, output reg [31:0] cycles);
    wire [3:0] d; wire [199:0] a0, a1, a2, a3;
    ldeep_eng #(.CODE_BASE(0),    .F_WCODE("deep_wcode_e0.hex"), .F_WCL("deep_wcl_e0.hex"), .F_HDR("deep_hdr_e0.hex"), .F_LITS("deep_lits_e0.hex")) e0 (clk, rst, wr_en, wr_addr, wr_bit, start, d[0], a0);
    ldeep_eng #(.CODE_BASE(1152), .F_WCODE("deep_wcode_e1.hex"), .F_WCL("deep_wcl_e1.hex"), .F_HDR("deep_hdr_e1.hex"), .F_LITS("deep_lits_e1.hex")) e1 (clk, rst, wr_en, wr_addr, wr_bit, start, d[1], a1);
    ldeep_eng #(.CODE_BASE(2304), .F_WCODE("deep_wcode_e2.hex"), .F_WCL("deep_wcl_e2.hex"), .F_HDR("deep_hdr_e2.hex"), .F_LITS("deep_lits_e2.hex")) e2 (clk, rst, wr_en, wr_addr, wr_bit, start, d[2], a2);
    ldeep_eng #(.CODE_BASE(3456), .F_WCODE("deep_wcode_e3.hex"), .F_WCL("deep_wcl_e3.hex"), .F_HDR("deep_hdr_e3.hex"), .F_LITS("deep_lits_e3.hex")) e3 (clk, rst, wr_en, wr_addr, wr_bit, start, d[3], a3);
    reg signed [19:0] tot [0:9]; genvar g; generate for (g = 0; g < 10; g = g + 1) begin : pk assign scores_flat[20*g +: 20] = tot[g]; end endgenerate
    reg [1:0] st; reg [3:0] k; reg signed [19:0] best; reg [3:0] bidx; integer j; reg started;
    always @(posedge clk) begin
        if (rst) begin st <= 0; busy <= 0; done <= 0; pred <= 0; cycles <= 0; started <= 0; end
        else begin
            done <= 0; if (busy) cycles <= cycles + 1;
            case (st)
                0: if (start) begin busy <= 1; cycles <= 0; started <= 0; st <= 1; end
                1: begin started <= 1; if (started && (&d)) begin for (j = 0; j < 10; j = j + 1) tot[j] <= $signed(a0[20*j +: 20]) + $signed(a1[20*j +: 20]) + $signed(a2[20*j +: 20]) + $signed(a3[20*j +: 20]); k <= 1; st <= 2; end end
                2: begin best <= tot[0]; bidx <= 0; k <= 1; st <= 3; end
                3: begin if (k == 10) begin pred <= bidx; done <= 1; busy <= 0; st <= 0; end else begin if (tot[k] > best) begin best <= tot[k]; bidx <= k; end k <= k + 1; end end
            endcase
        end
    end
endmodule
