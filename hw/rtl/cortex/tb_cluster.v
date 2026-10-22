// Testbench for cortex_cluster. cluster_in.hex (32-bit words): [0] NSn (pairs), then per pair: len, then its list; then RST*K init pair indices. Loads everything, pulses start, waits for done, writes "T total" and "G group" per pair to cluster_out.txt.
`timescale 1ns/1ps
module tb_cluster;
    parameter NB = 256, AW = 8, NS = 48, PW = 6, LM = 40, K = 4, CW = 8, ITER = 3, RST = 2, NMAX = 4000;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg lw_we = 0; reg [PW-1:0] lw_pair = 0; reg [7:0] lw_pos = 0; reg [AW-1:0] lw_val = 0; reg ln_we = 0; reg [PW-1:0] ln_pair = 0; reg [7:0] ln_val = 0; reg in_we = 0; reg [7:0] in_idx = 0; reg [PW-1:0] in_val = 0;
    reg start = 0; wire busy, done; reg [PW-1:0] rd_pair = 0; wire [3:0] rd_group; wire signed [31:0] tot_out;
    cortex_cluster #(.NB(NB), .AW(AW), .NS(NS), .PW(PW), .LM(LM), .K(K), .CW(CW), .ITER(ITER), .RST(RST)) U(.clk(clk), .rst(rst), .lw_we(lw_we), .lw_pair(lw_pair), .lw_pos(lw_pos), .lw_val(lw_val), .ln_we(ln_we), .ln_pair(ln_pair), .ln_val(ln_val),
        .in_we(in_we), .in_idx(in_idx), .in_val(in_val), .start(start), .busy(busy), .done(done), .rd_pair(rd_pair), .rd_group(rd_group), .tot_out(tot_out));
    reg [31:0] mem [0:NMAX]; integer f, p, n, q, len, cyc;
    initial begin
        $readmemh("cluster_in.hex", mem); f = $fopen("cluster_out.txt", "w"); repeat (3) @(negedge clk); rst = 0; p = 1;
        for (n = 0; n < mem[0]; n = n + 1) begin
            len = mem[p]; p = p + 1; @(negedge clk); ln_we = 1; ln_pair = n; ln_val = len; @(negedge clk); ln_we = 0;
            for (q = 0; q < len; q = q + 1) begin @(negedge clk); lw_we = 1; lw_pair = n; lw_pos = q; lw_val = mem[p + q]; end @(negedge clk); lw_we = 0; p = p + len;
        end
        
        @(negedge clk); start = 1; @(negedge clk); start = 0; cyc = 0; while (!done) begin @(negedge clk); cyc = cyc + 1; end
        $fdisplay(f, "T %0d", tot_out);
        for (n = 0; n < mem[0]; n = n + 1) begin rd_pair = n; @(negedge clk); @(negedge clk); $fdisplay(f, "G %0d", rd_group); end
        $fclose(f); $display("cycles %0d", cyc); $finish;
    end
endmodule
