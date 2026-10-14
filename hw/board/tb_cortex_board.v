// UART-level testbench for cortex_board_top: sends host bytes from in_cortex.hex, records every reply byte.
`timescale 1ns/1ps
module tb_cortex_board;
    parameter NBYTES = 1000, CPB = 16;
    reg clk = 0; always #18.5 clk = ~clk;                    // 27 MHz
    reg rx = 1'b1; wire tx; wire [5:0] led_n; wire trig;
    cortex_board_top #(.CLK_HZ(27_000_000), .BAUD(27_000_000 / CPB), .POR_BITS(4)) dut(
        .clk(clk), .btn_s1(1'b0), .btn_s2(1'b0), .uart_rx(rx), .uart_tx(tx), .led_n(led_n), .trig_out(trig));
    reg [7:0] bytes [0:NBYTES-1]; reg [15:0] expect_n [0:NBYTES-1];
    integer f, p, q, got, want;
    task send(input [7:0] v); integer t; begin
        rx = 0; repeat (CPB) @(posedge clk);
        for (t = 0; t < 8; t = t + 1) begin rx = v[t]; repeat (CPB) @(posedge clk); end
        rx = 1; repeat (CPB) @(posedge clk);
    end endtask
    // receiver: sample in the middle of each bit
    reg [7:0] rb; integer bi;
    initial begin
        f = $fopen("out_cortex_board.txt", "w"); got = 0;
        forever begin
            @(negedge tx); repeat (CPB / 2) @(posedge clk);
            for (bi = 0; bi < 8; bi = bi + 1) begin repeat (CPB) @(posedge clk); rb[bi] = tx; end
            repeat (CPB) @(posedge clk);
            $fdisplay(f, "%02x", rb); got = got + 1;
        end
    end
    initial begin
        $readmemh("in_cortex.hex", bytes); $readmemh("in_cortex_n.hex", expect_n);
        repeat (100) @(posedge clk);
        p = 0; q = 0; want = 0;
        while (p < NBYTES && bytes[p] !== 8'hxx) begin
            // expect_n[q] = number of bytes in this command, high bit set: wait for the reply count after it
            for (bi = 0; bi < expect_n[q][14:0]; bi = bi + 1) begin send(bytes[p]); p = p + 1; end
            want = want + expect_n[q + 1];
            while (got < want) @(posedge clk);
            q = q + 2;
        end
        repeat (200) @(posedge clk); $fclose(f); $display("bytes sent %0d, replies %0d, time %0t", p, got, $time); $finish;
    end
endmodule
