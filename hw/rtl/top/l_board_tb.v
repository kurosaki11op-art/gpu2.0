// Testbench for l_board_top: plays the host over a UART model (fast baud for simulation), sends NIMG images and one matmul request, records the reply bytes to out_board.txt.
`timescale 1ns/1ps
module l_board_tb;
    parameter NB = 6176, NIMG = 4, CPB = 16;
    reg clk = 0, rst = 1, rx = 1; wire tx, ld, lf;
    l_board_top #(.CLK_HZ(16*100000), .BAUD(100000)) dut (.clk(clk), .rst(rst), .rx(rx), .tx(tx), .led_deep(ld), .led_forge(lf));
    always #5 clk = ~clk;
    reg [NB-1:0] imgs [0:199]; reg [15:0] idx [0:NIMG-1]; integer n, f, k, b;
    task send_byte(input [7:0] d); integer i; begin rx = 0; repeat (CPB) @(posedge clk); for (i = 0; i < 8; i = i + 1) begin rx = d[i]; repeat (CPB) @(posedge clk); end rx = 1; repeat (CPB) @(posedge clk); end endtask
    task recv_byte(output [7:0] d); integer i; begin wait (tx == 0); repeat (CPB + CPB / 2) @(posedge clk); for (i = 0; i < 8; i = i + 1) begin d[i] = tx; repeat (CPB) @(posedge clk); end end endtask
    reg [7:0] rb; reg [31:0] rt;
    initial begin
        $readmemh("sys_in.hex", imgs); $readmemh("board_idx.hex", idx); f = $fopen("out_board.txt", "w"); repeat (5) @(posedge clk); rst = 0; repeat (5) @(posedge clk);
        if (!$value$plusargs("reject_t=%d", rt)) rt = 0;
        send_byte(8'hA5); send_byte(8'h03); send_byte(rt[7:0]); send_byte(rt[15:8]); send_byte({4'b0, rt[19:16]});   // SET_REJECT
        for (n = 0; n < NIMG; n = n + 1) begin
            send_byte(8'hA5); send_byte(8'h01);
            for (k = 0; k < 772; k = k + 1) begin send_byte({imgs[idx[n]][8*k+7], imgs[idx[n]][8*k+6], imgs[idx[n]][8*k+5], imgs[idx[n]][8*k+4], imgs[idx[n]][8*k+3], imgs[idx[n]][8*k+2], imgs[idx[n]][8*k+1], imgs[idx[n]][8*k]}); end
            for (b = 0; b < 7; b = b + 1) begin recv_byte(rb); $fwrite(f, "%0d ", rb); end $fwrite(f, "\n");
        end
        send_byte(8'hA5); send_byte(8'h02); for (b = 0; b < 5 + 256 * 5; b = b + 1) begin recv_byte(rb); $fwrite(f, "%0d ", rb); if (b >= 4 && ((b - 4) % 5) == 0) $fwrite(f, "\n"); end
        $fclose(f); $finish;
    end
endmodule
