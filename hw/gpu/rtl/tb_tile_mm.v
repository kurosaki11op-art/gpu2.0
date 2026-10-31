// testbench for tile_mm: +k= +m= +nb= (decimal), files wmem.hex (one LANES-byte word per line) and amem.hex (one byte per line); writes out.txt (row block then LANES 32-bit hex values) and prints CYCLES.
`timescale 1ns/1ps
module tb_tile_mm;
    parameter LANES = 64; reg clk = 0; reg rst = 1; reg start = 0; integer k, m, nb, cyc, fd;
    reg [11:0] kk, mm, nn; wire [19:0] w_addr, a_addr; reg [8*LANES-1:0] w_data; reg [7:0] a_data; wire out_valid, out_last, busy; wire [32*LANES-1:0] out_acc; wire [11:0] out_row, out_blk;
    reg [8*LANES-1:0] wmem [0:65535]; reg [7:0] amem [0:65535];
    tile_mm #(.LANES(LANES)) dut(clk, rst, start, kk, mm, nn, w_addr, w_data, a_addr, a_data, out_valid, out_acc, out_row, out_blk, out_last, busy);
    always #5 clk = ~clk;
    always @(posedge clk) begin w_data <= wmem[w_addr]; a_data <= amem[a_addr]; end   // synchronous memories, one cycle of latency
    always @(posedge clk) if (out_valid) begin $fdisplay(fd, "%0d %0d %h", out_row, out_blk, out_acc); end
    initial begin
        if (!$value$plusargs("k=%d", k)) k = 16; if (!$value$plusargs("m=%d", m)) m = 8; if (!$value$plusargs("nb=%d", nb)) nb = 1; kk = k; mm = m; nn = nb;
        $readmemh("wmem.hex", wmem); $readmemh("amem.hex", amem); fd = $fopen("out.txt", "w");
        repeat (3) @(posedge clk); rst <= 0; @(posedge clk); start <= 1; cyc = 0; @(posedge clk); start <= 0;   // nonblocking: no race with the DUT's clock edge
        while (!(out_valid && out_last) && cyc < 4000000) begin @(posedge clk); cyc = cyc + 1; end
        @(posedge clk); $fclose(fd); $display("CYCLES %0d", cyc + 1); $finish;
    end
endmodule
