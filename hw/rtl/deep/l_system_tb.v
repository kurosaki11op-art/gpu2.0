// Testbench for l_system: loads each image bit by bit, runs, writes routed flag, scores, prediction and cycles to out_sys.txt.
`timescale 1ns/1ps
module l_system_tb;
    parameter NB = 6176, NTEST = 200;
    reg clk = 0, rst = 1, start = 0, wr_en = 0; reg [12:0] wr_addr; reg wr_bit; wire busy, done, routed; wire [3:0] pred; wire [199:0] sc; wire [31:0] cycles;
    l_system dut (.clk(clk), .rst(rst), .wr_en(wr_en), .wr_addr(wr_addr), .wr_bit(wr_bit), .start(start), .busy(busy), .done(done), .routed(routed), .pred(pred), .scores_flat(sc), .cycles(cycles));
    always #5 clk = ~clk;
    reg [NB-1:0] imgs [0:NTEST-1]; integer n, f, j, a; reg signed [19:0] s;
    initial begin
        $readmemh("sys_in.hex", imgs); f = $fopen("out_sys.txt", "w"); repeat (3) @(posedge clk); rst = 0;
        for (n = 0; n < NTEST; n = n + 1) begin
            for (a = 0; a < NB; a = a + 1) begin @(negedge clk); wr_en = 1; wr_addr = a; wr_bit = imgs[n][a]; end
            @(negedge clk); wr_en = 0; start = 1; @(negedge clk); start = 0; wait (done); @(negedge clk);
            $fwrite(f, "%0d ", routed); for (j = 0; j < 10; j = j + 1) begin s = sc[20*j +: 20]; $fwrite(f, "%0d ", s); end
            $fwrite(f, "%0d %0d\n", pred, cycles);
        end
        $fclose(f); $finish;
    end
endmodule
