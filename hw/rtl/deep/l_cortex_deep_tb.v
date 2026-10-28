// Testbench for l_cortex_deep: loads detectors (tmpl.hex), the stage-1 table (deep_wcode1.hex), then N raw images (full_img.hex, 784 bytes each); writes
// "routed s0..s9 pred cycles enc core deep overlap" per image to out_full.txt. Inputs are driven on the falling edge.
`timescale 1ns/1ps
module l_cortex_deep_tb;
    parameter N = 4;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg tm_we = 0; reg [1:0] tm_ch = 0; reg [4:0] tm_f = 0; reg [24:0] tm_data = 0;
    reg tbl_we = 0; reg [12:0] tbl_addr = 0; reg [79:0] tbl_data = 0;
    reg pix_we = 0; reg [9:0] pix_addr = 0; reg [7:0] pix_data = 0; reg start = 0;
    wire busy, done, routed, err; wire [3:0] pred; wire [199:0] sc; wire [31:0] cycles, ce, cc, cd;
    l_cortex_deep dut (.clk(clk), .rst(rst), .tm_we(tm_we), .tm_ch(tm_ch), .tm_f(tm_f), .tm_data(tm_data), .tbl_we(tbl_we), .tbl_addr(tbl_addr), .tbl_data(tbl_data),
        .pix_we(pix_we), .pix_addr(pix_addr), .pix_data(pix_data), .start(start), .busy(busy), .done(done), .routed(routed), .pred(pred), .scores_flat(sc),
        .cycles(cycles), .cyc_enc(ce), .cyc_core(cc), .cyc_deep(cd), .err_overlap(err));
    reg [24:0] tmpl [0:127]; reg [79:0] tbl [0:4607]; reg [7:0] img [0:N*784-1];
    integer f, n, q, j;
    initial begin
        $readmemh("tmpl.hex", tmpl); $readmemh("deep_wcode1.hex", tbl); $readmemh("full_img.hex", img); f = $fopen("out_full.txt", "w");
        repeat (3) @(negedge clk); rst = 0;
        while (busy || !dut.init_done) @(negedge clk);
        for (q = 0; q < 128; q = q + 1) begin @(negedge clk); tm_we = 1; tm_ch = q / 32; tm_f = q % 32; tm_data = tmpl[q]; end
        @(negedge clk); tm_we = 0;
        for (q = 0; q < 4608; q = q + 1) begin
            @(negedge clk); tbl_we = 1; tbl_addr = q; tbl_data = tbl[q];
            @(negedge clk); tbl_we = 0; @(negedge clk); while (busy) @(negedge clk);
        end
        for (n = 0; n < N; n = n + 1) begin
            for (q = 0; q < 784; q = q + 1) begin @(negedge clk); pix_we = 1; pix_addr = q; pix_data = img[n * 784 + q]; end
            @(negedge clk); pix_we = 0; start = 1; @(negedge clk); start = 0;
            while (!done) @(negedge clk);
            $fwrite(f, "%0d", routed); for (j = 0; j < 10; j = j + 1) $fwrite(f, " %0d", $signed(sc[20*j +: 20]));
            $fdisplay(f, " %0d %0d %0d %0d %0d %0d", pred, cycles, ce, cc, cd, err);
        end
        $fclose(f); $display("images %0d, cycles total %0t", N, $time / 10); $finish;
    end
endmodule
