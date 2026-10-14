// Testbench for the ENC_LEARN encoder: learn from L images (img_learn.hex) with a reseed after image RS and one at
// the end, then encode N images (img.hex) with the learned detectors. Writes the counters (out_lc.txt, 128 words of
// 150 bits, {channel, detector}) and each test image's active code bits (out_enc.txt).
`timescale 1ns/1ps
module tb_cortex_encoder_learn;
    parameter L = 60, RS = 30, N = 10;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg pix_we = 0; reg [9:0] pix_addr = 0; reg [7:0] pix_data = 0;
    reg tm_we = 0; reg [1:0] tm_ch = 0; reg [4:0] tm_f = 0; reg [24:0] tm_data = 0; reg start = 0;
    reg learn = 0, lclear = 0, reseed = 0;
    wire busy, done, out_we; wire [13:0] count; wire [12:0] out_addr, out_data;
    cortex_encoder dut(.clk(clk), .rst(rst), .pix_we(pix_we), .pix_addr(pix_addr), .pix_data(pix_data),
        .tm_we(tm_we), .tm_ch(tm_ch), .tm_f(tm_f), .tm_data(tm_data), .start(start),
        .learn(learn), .lclear(lclear), .reseed(reseed),
        .busy(busy), .done(done), .count(count), .out_we(out_we), .out_addr(out_addr), .out_data(out_data));
    reg [7:0] limg [0:L*784-1]; reg [7:0] img [0:N*784-1];
    integer f, n, q, cyc0;
    always @(posedge clk) if (out_we) $fwrite(f, " %0d", out_data);
    task run_image; input integer base; input is_learn; begin
        for (q = 0; q < 784; q = q + 1) begin
            @(negedge clk); pix_we = 1; pix_addr = q; pix_data = is_learn ? limg[base + q] : img[base + q];
        end
        @(negedge clk); pix_we = 0; learn = is_learn; start = 1; cyc0 = $time / 10;
        @(negedge clk); start = 0;
        while (!done) @(negedge clk);
    end endtask
    task do_reseed; begin
        @(negedge clk); reseed = 1; @(negedge clk); reseed = 0;
        while (!done) @(negedge clk);
    end endtask
    initial begin
        $readmemh("img_learn.hex", limg); $readmemh("img.hex", img); f = $fopen("out_enc.txt", "w");
        repeat (3) @(negedge clk); rst = 0;
        @(negedge clk); lclear = 1; @(negedge clk); lclear = 0;
        for (n = 0; n < L; n = n + 1) begin
            run_image(n * 784, 1);
            if (n == 0) $display("learning cycles per image %0d", $time / 10 - cyc0);
            if (n == RS - 1) do_reseed;
        end
        do_reseed;
        for (n = 0; n < N; n = n + 1) begin run_image(n * 784, 0); $fwrite(f, "\n"); end
        $fclose(f);
        f = $fopen("out_lc.txt", "w");
        for (q = 0; q < 128; q = q + 1) $fwrite(f, "%038h\n", dut.lc[q]);
        $fclose(f); $finish;
    end
endmodule
