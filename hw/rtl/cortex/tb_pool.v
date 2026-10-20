// Testbench: loads pool_in.hex (known mask, nslots, then per slot: C scores, K neighbour slots, the ear's name), runs the pooling, writes the new names to pool_out.txt.
`timescale 1ns/1ps
module tb_pool;
    parameter NS = 32, SW = 5, C = 10, K = 8, EV = 200;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg sc_we = 0; reg [SW-1:0] sc_slot = 0; reg [3:0] sc_class = 0; reg signed [19:0] sc_val = 0;
    reg nbw_we = 0; reg [SW-1:0] nbw_slot = 0; reg [3:0] nbw_k = 0; reg [SW-1:0] nbw_id = 0; reg nm_we = 0; reg [SW-1:0] nm_slot = 0; reg [3:0] nm_val = 0;
    reg [C-1:0] known = 0; reg [SW:0] nslots = 0; reg start = 0; wire busy, done; reg [SW-1:0] rd_slot = 0; wire [3:0] rd_name;
    cortex_pool #(.NS(NS), .SW(SW), .C(C), .K(K), .EV(EV)) dut(.clk(clk), .rst(rst), .sc_we(sc_we), .sc_slot(sc_slot), .sc_class(sc_class), .sc_val(sc_val), .nbw_we(nbw_we), .nbw_slot(nbw_slot), .nbw_k(nbw_k), .nbw_id(nbw_id),
        .nm_we(nm_we), .nm_slot(nm_slot), .nm_val(nm_val), .known(known), .nslots(nslots), .start(start), .busy(busy), .done(done), .rd_slot(rd_slot), .rd_name(rd_name));
    reg [31:0] mem [0:NS*(C+K+1)+3]; integer f, s, c, k, p, cyc;
    initial begin
        $readmemh("pool_in.hex", mem); f = $fopen("pool_out.txt", "w"); repeat (3) @(negedge clk); rst = 0;
        known = mem[0]; nslots = mem[1]; p = 2;
        for (s = 0; s < nslots; s = s + 1) begin
            for (c = 0; c < C; c = c + 1) begin @(negedge clk); sc_we = 1; sc_slot = s; sc_class = c; sc_val = mem[p]; p = p + 1; end
            for (k = 0; k < K; k = k + 1) begin @(negedge clk); sc_we = 0; nbw_we = 1; nbw_slot = s; nbw_k = k; nbw_id = mem[p]; p = p + 1; end
            @(negedge clk); nbw_we = 0; nm_we = 1; nm_slot = s; nm_val = mem[p]; p = p + 1; @(negedge clk); nm_we = 0;
        end
        @(negedge clk); start = 1; @(negedge clk); start = 0; cyc = 0; while (!done) begin @(negedge clk); cyc = cyc + 1; end
        for (s = 0; s < nslots; s = s + 1) begin rd_slot = s; @(negedge clk); @(negedge clk); $fdisplay(f, "%0d", rd_name); end
        $fclose(f); $display("slots %0d, cycles %0d", nslots, cyc); $finish;
    end
endmodule
