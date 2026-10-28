// Testbench for ldeep_core_bram: loads each routed image bit by bit, starts the core, writes scores, prediction and cycles to out_deep_p.txt.
`timescale 1ns/1ps
module ldeep_p_tb;
    parameter NB = 6176, NTEST = 300;
    reg clk = 0, rst = 1, start = 0, wr_en = 0; reg [12:0] wr_addr; reg wr_bit; wire busy, done; wire [3:0] pred; wire [199:0] sc; wire [31:0] cycles;
    ldeep_core_p dut (.clk(clk), .rst(rst), .wr_en(wr_en), .wr_addr(wr_addr), .wr_bit(wr_bit), .start(start), .busy(busy), .done(done), .pred(pred), .scores_flat(sc), .cycles(cycles));
    always #5 clk = ~clk;
    reg [NB-1:0] imgs [0:NTEST-1]; integer n, f, j, a; reg signed [19:0] s;
    initial begin
        $readmemh("deep_in.hex", imgs); f = $fopen("out_deep_p.txt", "w"); repeat (3) @(posedge clk); rst = 0;
        for (n = 0; n < NTEST; n = n + 1) begin
            for (a = 0; a < NB; a = a + 1) begin @(negedge clk); wr_en = 1; wr_addr = a; wr_bit = imgs[n][a]; end
            @(negedge clk); wr_en = 0; start = 1; @(negedge clk); start = 0; wait (done); @(negedge clk);
            for (j = 0; j < 10; j = j + 1) begin s = sc[20*j +: 20]; $fwrite(f, "%0d ", s); end
            $fwrite(f, "%0d %0d\n", pred, cycles);
        end
        $fclose(f); $finish;
    end
endmodule
