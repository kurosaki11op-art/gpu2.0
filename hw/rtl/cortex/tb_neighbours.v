// Testbench: loads slots from nb_codes.hex (per slot: length, then LWMAX entries), runs the queries listed in nb_q.hex, writes the K neighbours (slot, overlap) of each query to nb_out.txt.
`timescale 1ns/1ps
module tb_neighbours;
    parameter NS = 16, SW = 4, LW = 10, K = 4, NQ = 4, LWMAX = 1024;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg nw_we = 0; reg [SW-1:0] nw_slot = 0; reg [LW-1:0] nw_addr = 0; reg [13:0] nw_data = 0; reg len_we = 0; reg [SW-1:0] len_slot = 0; reg [LW:0] len_val = 0; reg start = 0; reg [SW-1:0] qslot = 0;
    wire busy, done; wire [K*SW-1:0] nb_id; wire [K*(LW+1)-1:0] nb_ov;
    cortex_neighbours #(.NS(NS), .SW(SW), .LW(LW), .K(K)) dut(.clk(clk), .rst(rst), .nw_we(nw_we), .nw_slot(nw_slot), .nw_addr(nw_addr), .nw_data(nw_data), .len_we(len_we), .len_slot(len_slot), .len_val(len_val),
        .start(start), .qslot(qslot), .busy(busy), .done(done), .nb_id(nb_id), .nb_ov(nb_ov));
    reg [31:0] codes [0:NS*(LWMAX+1)-1]; reg [31:0] qs [0:NQ-1]; integer f, s, a, k, n, cyc;
    initial begin
        $readmemh("nb_codes.hex", codes); $readmemh("nb_q.hex", qs); f = $fopen("nb_out.txt", "w");
        repeat (3) @(negedge clk); rst = 0;
        for (s = 0; s < NS; s = s + 1) begin
            n = codes[s * (LWMAX + 1)];
            for (a = 0; a < n; a = a + 1) begin @(negedge clk); nw_we = 1; nw_slot = s; nw_addr = a; nw_data = codes[s * (LWMAX + 1) + 1 + a]; end
            @(negedge clk); nw_we = 0; len_we = 1; len_slot = s; len_val = n; @(negedge clk); len_we = 0;
        end
        for (s = 0; s < NQ; s = s + 1) begin
            @(negedge clk); qslot = qs[s]; start = 1; @(negedge clk); start = 0; cyc = 0;
            while (!done) begin @(negedge clk); cyc = cyc + 1; end
            for (k = 0; k < K; k = k + 1) $fwrite(f, "%0d %0d ", nb_id[k*SW +: SW], nb_ov[k*(LW+1) +: (LW+1)]);
            $fwrite(f, "\n");
        end
        $fclose(f); $display("queries %0d, last query cycles %0d", NQ, cyc); $finish;
    end
endmodule
