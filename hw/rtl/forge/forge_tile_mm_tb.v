`timescale 1ns/1ps
module forge_tile_mm_tb;
    parameter M = 16, N = 16, NB = 8;
    reg clk = 0, rst = 1, start = 0; wire busy, done; wire [31:0] cycles; reg [$clog2(M*N)-1:0] ra; wire signed [16:0] cm; wire signed [11:0] ce;
    forge_tile_mm #(M, N, NB) dut (.clk(clk), .rst(rst), .start(start), .busy(busy), .done(done), .cycles(cycles), .c_raddr(ra), .c_macc(cm), .c_eacc(ce));
    always #5 clk = ~clk; integer f, k;
    initial begin
        repeat (3) @(posedge clk); rst = 0; @(negedge clk); start = 1; @(negedge clk); start = 0; wait (done); repeat (3) @(negedge clk);
        f = $fopen("out_mm.txt", "w");
        for (k = 0; k < M*N; k = k + 1) begin ra = k; repeat (3) @(negedge clk); $fwrite(f, "%0d %0d\n", cm, ce); end
        $fwrite(f, "cycles %0d\n", cycles); $fclose(f); $finish;
    end
endmodule
