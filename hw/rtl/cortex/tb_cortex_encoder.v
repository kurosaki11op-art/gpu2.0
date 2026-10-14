// Testbench: encode N images (img.hex, 784 bytes each) with detectors from tmpl.hex (128 words of 25 bits,
// channel-major), print each image's active code bits to out_enc.txt.
`timescale 1ns/1ps
module tb_cortex_encoder;
    parameter N = 10;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg pix_we = 0; reg [9:0] pix_addr = 0; reg [7:0] pix_data = 0;
    reg tm_we = 0; reg [1:0] tm_ch = 0; reg [4:0] tm_f = 0; reg [24:0] tm_data = 0; reg start = 0;
    wire busy, done, out_we; wire [13:0] count; wire [12:0] out_addr, out_data;
    cortex_encoder dut(.clk(clk), .rst(rst), .pix_we(pix_we), .pix_addr(pix_addr), .pix_data(pix_data),
        .tm_we(tm_we), .tm_ch(tm_ch), .tm_f(tm_f), .tm_data(tm_data), .start(start),
        .busy(busy), .done(done), .count(count), .out_we(out_we), .out_addr(out_addr), .out_data(out_data));
    reg [7:0] img [0:N*784-1]; reg [24:0] tmpl [0:127];
    integer f, n, q, cyc0;
    always @(posedge clk) if (out_we) $fwrite(f, " %0d", out_data);
    initial begin
        $readmemh("img.hex", img); $readmemh("tmpl.hex", tmpl); f = $fopen("out_enc.txt", "w");
        repeat (3) @(negedge clk); rst = 0;
        for (q = 0; q < 128; q = q + 1) begin @(negedge clk); tm_we = 1; tm_ch = q / 32; tm_f = q % 32; tm_data = tmpl[q]; end
        @(negedge clk); tm_we = 0;
        for (n = 0; n < N; n = n + 1) begin
            for (q = 0; q < 784; q = q + 1) begin @(negedge clk); pix_we = 1; pix_addr = q; pix_data = img[n * 784 + q]; end
            @(negedge clk); pix_we = 0; start = 1; cyc0 = $time / 10;
            @(negedge clk); start = 0;
            while (!done) @(negedge clk);
            $fwrite(f, "\n"); if (n == 0) $display("cycles per image %0d", $time / 10 - cyc0);
        end
        $fclose(f); $finish;
    end
endmodule
