// Bit-bangs the UART of tile_board_top (fast clock/baud for simulation): update then lookup of a few words, checks the 9-byte reply.  (the behavioural bank starts with the pattern i*40503+(i>>3), so word 3 = DAA5 and the update adds 0A07 per byte: expect E4AC)
`timescale 1ns/1ps
module tb_tile_board;
    localparam CLK_HZ = 1_000_000, BAUD = 100_000, BIT = CLK_HZ / BAUD;
    reg clk = 0, rx = 1; always #500 clk = ~clk; wire tx;
    tile_board_top #(.CLK_HZ(CLK_HZ), .BAUD(BAUD), .POR_BITS(4), .AW(8)) dut (.clk(clk), .btn_s1(1'b0), .btn_s2(1'b0), .uart_rx(rx), .uart_tx(tx), .led_n(), .trig_out());
    task sendb(input [7:0] b); integer k; begin rx = 0; repeat (BIT) @(posedge clk); for (k = 0; k < 8; k = k + 1) begin rx = b[k]; repeat (BIT) @(posedge clk); end rx = 1; repeat (BIT) @(posedge clk); end endtask
    reg [7:0] got [0:15]; integer gi = 0, errs = 0, i;
    always @(negedge tx) begin : rcv integer k; reg [7:0] v; repeat (BIT + BIT / 2) @(posedge clk); for (k = 0; k < 8; k = k + 1) begin v[k] = tx; repeat (BIT) @(posedge clk); end got[gi] = v; gi = gi + 1; end
    task flit(input [1:0] ty, input [17:0] a, input [31:0] d); reg [71:0] f; integer k; begin f = {ty, 6'd0, 6'd0, 8'd5, a, d}; sendb(8'h54); for (k = 8; k >= 0; k = k - 1) sendb(f[8*k +: 8]); end endtask
    initial begin
        repeat (600) @(posedge clk);
        sendb(8'h45); repeat (3 * BIT * 10) @(posedge clk); if (got[0] !== 8'h5A) begin errs = errs + 1; $display("ping fail %h", got[0]); end
        gi = 0; flit(2'd2, 18'd3, 32'h0000_0A07); repeat (40 * BIT) @(posedge clk); if (got[0] !== 8'h4B) begin errs = errs + 1; $display("ack fail %h", got[0]); end
        gi = 0; flit(2'd0, 18'd3, 32'd0); repeat (140 * BIT) @(posedge clk);
        if (gi !== 9 || got[7] !== 8'hE4 || got[8] !== 8'hAC) begin errs = errs + 1; $display("lookup fail gi=%0d %h %h", gi, got[7], got[8]); end
        if (errs == 0) $display("TILE BOARD PASS"); else $display("TILE BOARD FAIL %0d", errs); $finish; end
endmodule
