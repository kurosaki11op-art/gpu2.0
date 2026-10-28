// Testbench for ldeep_core: reads routed test images (deep_in.hex), runs each, writes scores, prediction and cycles to out_deep.txt.
`timescale 1ns/1ps
module ldeep_tb;
    parameter NB = 6176, NTEST = 300;
    reg clk = 0, rst = 1, start = 0; reg [NB-1:0] in_bits; wire busy, done; wire [3:0] pred; wire [199:0] sc; wire [31:0] cycles;
    ldeep_core dut (.clk(clk), .rst(rst), .start(start), .in_bits(in_bits), .busy(busy), .done(done), .pred(pred), .scores_flat(sc), .cycles(cycles));
    always #5 clk = ~clk;
    reg [NB-1:0] imgs [0:NTEST-1]; integer n, f, j; reg signed [19:0] s;
    initial begin
        $readmemh("deep_in.hex", imgs); f = $fopen("out_deep.txt", "w"); repeat (3) @(posedge clk); rst = 0;
        for (n = 0; n < NTEST; n = n + 1) begin
            @(negedge clk); in_bits = imgs[n]; start = 1; @(negedge clk); start = 0; wait (done); @(negedge clk);
            for (j = 0; j < 10; j = j + 1) begin s = sc[20*j +: 20]; $fwrite(f, "%0d ", s); end
            $fwrite(f, "%0d %0d\n", pred, cycles);
        end
        $fclose(f); $finish;
    end
endmodule
