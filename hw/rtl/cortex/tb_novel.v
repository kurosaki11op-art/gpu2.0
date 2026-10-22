// Testbench for cortex_novel: novel_in.hex: [0] n, [1] number of calibration scores Nc, Nc signed 20-bit scores, then [Nc+2] number of test scores M and M scores. Writes the threshold, then "score flag" per test score.
`timescale 1ns/1ps
module tb_novel;
    parameter SW = 20, NMAX = 20000;
    reg clk = 0, rst = 1; always #5 clk = ~clk; reg cal = 0; reg signed [SW-1:0] top = 0; reg [4:0] n = 0; wire signed [SW-1:0] thr; wire flag;
    cortex_novel #(.SW(SW)) U(.clk(clk), .rst(rst), .cal(cal), .top(top), .n(n), .thr(thr), .flag(flag));
    reg [31:0] mem [0:NMAX]; integer f, Nc, M, i, p;
    initial begin
        $readmemh("novel_in.hex", mem); f = $fopen("novel_out.txt", "w"); n = mem[0]; Nc = mem[1]; p = 2; repeat (3) @(negedge clk); rst = 0;
        for (i = 0; i < Nc; i = i + 1) begin @(negedge clk); top = mem[p + i]; cal = 1; @(negedge clk); cal = 0; end
        p = p + Nc; M = mem[p]; p = p + 1; @(negedge clk); $fdisplay(f, "T %0d", thr);
        for (i = 0; i < M; i = i + 1) begin top = mem[p + i]; #1; $fdisplay(f, "F %0d %0d", $signed(top), flag); end
        $fclose(f); $display("done"); $finish;
    end
endmodule
