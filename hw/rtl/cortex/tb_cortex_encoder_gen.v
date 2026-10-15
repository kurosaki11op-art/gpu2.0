// Testbench for cortex_encoder_gen: N pictures (img.hex) with detectors tmpl.hex (NCH*F words, channel-major);
// each picture's active code bits go to out_enc.txt, one line per picture.
`timescale 1ns/1ps
module tb_cortex_encoder_gen;
    parameter N = 4, NCH = 4, F = 32, LF = 5;
    parameter [8*NCH-1:0] THR = {8'd8, 8'd8, 8'd150, 8'd50};
    parameter [2*NCH-1:0] KIND = {2'd2, 2'd1, 2'd0, 2'd0};
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg pix_we = 0; reg [9:0] pix_addr = 0; reg [7:0] pix_data = 0;
    reg tm_we = 0; reg [LF+3:0] tm_addr = 0; reg [24:0] tm_data = 0; reg start = 0;
    wire busy, done, out_we; wire [15:0] count; wire [14:0] out_addr, out_data;
    cortex_encoder_gen #(.NCH(NCH), .F(F), .LF(LF), .THR(THR), .KIND(KIND)) dut(.clk(clk), .rst(rst),
        .pix_we(pix_we), .pix_addr(pix_addr), .pix_data(pix_data), .tm_we(tm_we), .tm_addr(tm_addr), .tm_data(tm_data),
        .start(start), .busy(busy), .done(done), .count(count), .out_we(out_we), .out_addr(out_addr), .out_data(out_data));
    reg [7:0] img [0:N*784-1]; reg [24:0] tmpl [0:NCH*F-1];
    integer f, n, q, t0;
    always @(posedge clk) if (out_we) $fwrite(f, " %0d", out_data);
    initial begin
        $readmemh("img.hex", img); $readmemh("tmpl.hex", tmpl); f = $fopen("out_enc.txt", "w");
        repeat (3) @(negedge clk); rst = 0;
        for (q = 0; q < NCH * F; q = q + 1) begin @(negedge clk); tm_we = 1; tm_addr = q; tm_data = tmpl[q]; end
        @(negedge clk); tm_we = 0;
        for (n = 0; n < N; n = n + 1) begin
            for (q = 0; q < 784; q = q + 1) begin @(negedge clk); pix_we = 1; pix_addr = q; pix_data = img[n * 784 + q]; end
            @(negedge clk); pix_we = 0; start = 1; t0 = $time; @(negedge clk); start = 0;
            while (!done) @(negedge clk);
            @(negedge clk);
            $fwrite(f, "\n"); if (n == 0) $display("cycles per picture %0d", ($time - t0) / 10);
        end
        $fclose(f); $finish;
    end
endmodule
