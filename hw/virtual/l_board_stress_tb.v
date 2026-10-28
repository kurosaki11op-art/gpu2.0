// Stress testbench for l_board_top: plays a scripted byte stream from host.hex (need.hex gives, per byte, how many reply bytes must have come back before it is sent: the protocol has no flow control, so a host must wait for each reply) (junk, invalid ops, truncated-looking frames, valid jobs) over a UART model while a
// parallel process records every byte the board sends back to out_board_stress.txt (hex, one per line). Fast baud for simulation.
`timescale 1ns/1ps
module l_board_stress_tb;
    parameter NHOST = 100, CPB = 16, WAIT_CYCLES = 3000000;
    reg clk = 0, rst = 1, rx = 1; wire tx, ld, lf;
    l_board_top #(.CLK_HZ(16*100000), .BAUD(100000)) dut (.clk(clk), .rst(rst), .rx(rx), .tx(tx), .led_deep(ld), .led_forge(lf));
    always #5 clk = ~clk; reg [7:0] host [0:NHOST-1]; reg [31:0] need [0:NHOST-1]; integer k, f, rcount = 0;
    task send_byte(input [7:0] d); integer i; begin rx = 0; repeat (CPB) @(posedge clk); for (i = 0; i < 8; i = i + 1) begin rx = d[i]; repeat (CPB) @(posedge clk); end rx = 1; repeat (CPB) @(posedge clk); end endtask
    reg [7:0] rb; integer i2;
    initial begin
        f = $fopen("out_board_stress.txt", "w");
        forever begin wait (tx == 0); repeat (CPB + CPB / 2) @(posedge clk); for (i2 = 0; i2 < 8; i2 = i2 + 1) begin rb[i2] = tx; repeat (CPB) @(posedge clk); end $fwrite(f, "%02x\n", rb); rcount = rcount + 1; end
    end
    initial begin
        $readmemh("host.hex", host); $readmemh("need.hex", need); repeat (5) @(posedge clk); rst = 0; repeat (5) @(posedge clk);
        for (k = 0; k < NHOST; k = k + 1) begin wait (rcount >= need[k]); send_byte(host[k]); end
        repeat (WAIT_CYCLES) @(posedge clk); $fflush(f); $fclose(f); $finish;
    end
endmodule
