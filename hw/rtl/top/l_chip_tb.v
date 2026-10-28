// Testbench for l_chip_top: 40 recognitions (images from sys_in.hex, expected routed flag, scores and prediction from sys_exp.txt) and one matrix product;
// writes per-job results and the number of cycles each layer was awake.
`timescale 1ns/1ps
module l_chip_tb;
    parameter NB = 6176, NIMG = 40;
    reg clk = 0, rst = 1, op = 0, start = 0, wr_en = 0; reg [12:0] wr_addr; reg wr_bit; reg [7:0] ra; wire busy, done, routed, ca, da, fa; wire [3:0] pred; wire [199:0] sc; wire signed [16:0] cm; wire signed [11:0] ce;
    l_chip_top dut (.clk(clk), .rst(rst), .op(op), .start(start), .wr_en(wr_en), .wr_addr(wr_addr), .wr_bit(wr_bit), .busy(busy), .done(done), .routed(routed), .pred(pred), .scores_flat(sc),
                    .cortex_active(ca), .deep_active(da), .forge_active(fa), .c_raddr(ra), .c_macc(cm), .c_eacc(ce), .cycles());
    always #5 clk = ~clk;
    reg [NB-1:0] imgs [0:NIMG-1]; integer n, f, j, a, k; integer cyc_c = 0, cyc_d = 0, cyc_f = 0, cyc_all = 0; reg signed [19:0] s;
    always @(posedge clk) if (!rst) begin cyc_all <= cyc_all + 1; if (ca) cyc_c <= cyc_c + 1; if (da) cyc_d <= cyc_d + 1; if (fa) cyc_f <= cyc_f + 1; end
    initial begin
        $readmemh("sys_in.hex", imgs); f = $fopen("out_top.txt", "w"); repeat (3) @(posedge clk); rst = 0;
        for (n = 0; n < NIMG; n = n + 1) begin
            op = 0; for (a = 0; a < NB; a = a + 1) begin @(negedge clk); wr_en = 1; wr_addr = a; wr_bit = imgs[n][a]; end
            @(negedge clk); wr_en = 0; start = 1; @(negedge clk); start = 0; wait (done); @(negedge clk);
            $fwrite(f, "R %0d ", routed); for (j = 0; j < 10; j = j + 1) begin s = sc[20*j +: 20]; $fwrite(f, "%0d ", s); end $fwrite(f, "%0d\n", pred);
        end
        op = 1; @(negedge clk); start = 1; @(negedge clk); start = 0; wait (done); repeat (3) @(negedge clk);
        for (k = 0; k < 256; k = k + 1) begin ra = k; repeat (3) @(negedge clk); $fwrite(f, "M %0d %0d\n", cm, ce); end
        $fwrite(f, "ACTIVE cortex %0d deep %0d forge %0d total %0d\n", cyc_c, cyc_d, cyc_f, cyc_all); $fclose(f); $finish;
    end
endmodule
