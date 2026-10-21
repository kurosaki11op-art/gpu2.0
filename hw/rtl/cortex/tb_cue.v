// Testbench for cortex_cue: cue_in.hex = per case: known mask, C scores of A, C scores of B (20-bit fields), then once at the top: 7 thresholds of A and of B. Writes pred and the two indices per case to cue_out.txt.
`timescale 1ns/1ps
module tb_cue;
    parameter NCASE = 100, C = 10, SW = 20;
    reg [C*SW-1:0] sa, sb; reg [C-1:0] known; reg [7*(SW+1)-1:0] ta, tb; wire [3:0] pred; wire [2:0] ia, ib;
    cortex_cue #(.C(C), .SW(SW)) dut(.sa(sa), .sb(sb), .known(known), .ta(ta), .tb(tb), .pred(pred), .ia_o(ia), .ib_o(ib));
    reg [31:0] mem [0:14 + NCASE * (2 * C + 1)]; integer f, n, c, p, q;
    initial begin
        $readmemh("cue_in.hex", mem); f = $fopen("cue_out.txt", "w"); p = 0;
        for (q = 0; q < 7; q = q + 1) begin ta[q*(SW+1) +: (SW+1)] = mem[p]; p = p + 1; end
        for (q = 0; q < 7; q = q + 1) begin tb[q*(SW+1) +: (SW+1)] = mem[p]; p = p + 1; end
        for (n = 0; n < NCASE; n = n + 1) begin
            known = mem[p]; p = p + 1;
            for (c = 0; c < C; c = c + 1) begin sa[c*SW +: SW] = mem[p]; p = p + 1; end
            for (c = 0; c < C; c = c + 1) begin sb[c*SW +: SW] = mem[p]; p = p + 1; end
            #1; $fdisplay(f, "%0d %0d %0d", pred, ia, ib);
        end
        $fclose(f); $display("cases %0d", NCASE); $finish;
    end
endmodule
