// Stress testbench for l_chip_top: a scripted mix of jobs (read from jobs.hex, 64-bit words {type 8 bits, arg 24 bits, arg2 32 bits}).
// type 0: recognise image arg; type 1: matrix product; type 2: start image arg, then reset the chip after arg2 cycles (a fault injection), no result.
// Writes one line per result: R routed scores pred, M plus 256 output lines, X for a reset.
`timescale 1ns/1ps
module l_chip_stress_tb;
    parameter NB = 6176, NJOB = 60, NIMG = 64;
    reg clk = 0, rst = 1, op = 0, start = 0, wr_en = 0; reg [12:0] wr_addr; reg wr_bit; reg [7:0] ra; wire busy, done, routed, ca, da, fa; wire [3:0] pred; wire [199:0] sc; wire signed [16:0] cm; wire signed [11:0] ce;
    l_chip_top dut (.clk(clk), .rst(rst), .op(op), .start(start), .wr_en(wr_en), .wr_addr(wr_addr), .wr_bit(wr_bit), .busy(busy), .done(done), .routed(routed), .pred(pred), .scores_flat(sc),
                    .cortex_active(ca), .deep_active(da), .forge_active(fa), .c_raddr(ra), .c_macc(cm), .c_eacc(ce), .cycles());
    always #5 clk = ~clk;
    reg [NB-1:0] imgs [0:NIMG-1]; reg [63:0] jobs [0:NJOB-1]; integer n, f, j, a, k; reg signed [19:0] s; reg [7:0] jt; reg [23:0] ja; reg [31:0] jb;
    integer cyc_c = 0, cyc_d = 0, cyc_f = 0; always @(posedge clk) begin if (ca) cyc_c <= cyc_c + 1; if (da) cyc_d <= cyc_d + 1; if (fa) cyc_f <= cyc_f + 1; end
    task load_image(input [23:0] idx); begin op = 0; for (a = 0; a < NB; a = a + 1) begin @(negedge clk); wr_en = 1; wr_addr = a; wr_bit = imgs[idx][a]; end @(negedge clk); wr_en = 0; end endtask
    initial begin
        $readmemh("stress_in.hex", imgs); $readmemh("jobs.hex", jobs); f = $fopen("out_stress.txt", "w"); repeat (3) @(posedge clk); rst = 0;
        for (n = 0; n < NJOB; n = n + 1) begin
            jt = jobs[n][63:56]; ja = jobs[n][55:32]; jb = jobs[n][31:0];
            if (jt == 0) begin
                load_image(ja); start = 1; @(negedge clk); start = 0; wait (done); @(negedge clk);
                $fwrite(f, "R %0d ", routed); for (j = 0; j < 10; j = j + 1) begin s = sc[20*j +: 20]; $fwrite(f, "%0d ", s); end $fwrite(f, "%0d\n", pred);
            end else if (jt == 1) begin
                op = 1; @(negedge clk); start = 1; @(negedge clk); start = 0; wait (done); repeat (3) @(negedge clk);
                $fwrite(f, "M\n"); for (k = 0; k < 256; k = k + 1) begin ra = k; repeat (3) @(negedge clk); $fwrite(f, "%0d %0d\n", cm, ce); end
            end else begin
                load_image(ja); start = 1; @(negedge clk); start = 0; repeat (jb) @(negedge clk); rst = 1; repeat (3) @(negedge clk); rst = 0; repeat (2) @(negedge clk); $fwrite(f, "X\n");
            end
        end
        $fwrite(f, "ACTIVE cortex %0d deep %0d forge %0d\n", cyc_c, cyc_d, cyc_f); $fclose(f); $finish;
    end
endmodule
