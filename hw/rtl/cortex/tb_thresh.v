// Testbench for cortex_quant and cortex_cuethr. thresh_in.hex: [0] n, [1] number of samples N, N samples, then [N+2] number of refs M and M refs. Writes the tracker output after every sample, then the 7 thresholds of every ref to thresh_out.txt.
`timescale 1ns/1ps
module tb_thresh;
    parameter W = 21, E0 = 9, K = 7, NMAX = 20000;
    reg clk = 0, rst = 1; always #5 clk = ~clk; reg valid = 0; reg [W-1:0] x = 0; reg [4:0] n = 0; wire [W-1:0] q; wire [19:0] cnt;
    cortex_quant #(.W(W), .E0(E0), .K(K)) U(.clk(clk), .rst(rst), .valid(valid), .x(x), .n(n), .q(q), .cnt(cnt));
    reg [W-1:0] ref = 0; wire [7*W-1:0] t; cortex_cuethr #(.W(W)) V(.ref(ref), .t(t));
    reg [31:0] mem [0:NMAX]; integer f, N, M, i, j, p;
    initial begin
        $readmemh("thresh_in.hex", mem); f = $fopen("thresh_out.txt", "w"); n = mem[0]; N = mem[1]; p = 2; repeat (3) @(negedge clk); rst = 0;
        for (i = 0; i < N; i = i + 1) begin @(negedge clk); x = mem[p + i]; valid = 1; @(negedge clk); valid = 0; $fdisplay(f, "Q %0d", q); end
        p = p + N; M = mem[p]; p = p + 1;
        for (i = 0; i < M; i = i + 1) begin ref = mem[p + i]; #1; $fwrite(f, "T"); for (j = 0; j < 7; j = j + 1) $fwrite(f, " %0d", t[j*W +: W]); $fwrite(f, "\n"); end
        $fclose(f); $display("done"); $finish;
    end
endmodule
