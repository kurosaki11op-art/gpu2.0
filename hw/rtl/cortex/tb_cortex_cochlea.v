// Testbench: N clips (smp.hex, 16,000 16-bit samples each) through cortex_cochlea; pixels to out_coch.txt (one line per clip).
`timescale 1ns/1ps
module tb_cortex_cochlea;
    parameter N = 2;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg smp_we = 0; reg [13:0] smp_addr = 0; reg [15:0] smp_data = 0; reg start = 0;
    wire busy, done, px_we; wire [9:0] px_addr; wire [7:0] px_data;
    cortex_cochlea dut(.clk(clk), .rst(rst), .smp_we(smp_we), .smp_addr(smp_addr), .smp_data(smp_data), .start(start),
        .busy(busy), .done(done), .px_we(px_we), .px_addr(px_addr), .px_data(px_data));
    reg [15:0] mem [0:N*16000-1];
    integer f, c, q, t0;
    always @(posedge clk) if (px_we) $fwrite(f, " %0d", px_data);
    initial begin
        $readmemh("smp.hex", mem); f = $fopen("out_coch.txt", "w");
        repeat (3) @(negedge clk); rst = 0;
        for (c = 0; c < N; c = c + 1) begin
            for (q = 0; q < 16000; q = q + 1) begin @(negedge clk); smp_we = 1; smp_addr = q; smp_data = mem[c * 16000 + q]; end
            @(negedge clk); smp_we = 0; start = 1; t0 = $time; @(negedge clk); start = 0;
            while (!done) @(negedge clk);
            @(negedge clk);                                   // the last pixel is written on this edge
            $fwrite(f, "\n"); if (c == 0) $display("cycles per clip %0d", ($time - t0) / 10);
        end
        $fclose(f); $finish;
    end
endmodule
