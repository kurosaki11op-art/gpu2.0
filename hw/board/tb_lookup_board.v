`timescale 1ns/1ps
// tb_lookup_board.v -- end-to-end test of lookup_board_top through a bit-level UART model.
// Writes every byte the board sends to rx_lookup.txt; check_lookup_board.py compares them with the reference model.
// Run from hw/board:  python check_lookup_board.py
module tb_lookup_board;
    localparam CLK_HZ = 1_000_000, BAUD = 100_000;   // 10 clocks per bit (simulation speed-up)
    localparam CPB = CLK_HZ / BAUD;
    parameter N1 = 40, N2 = 200;                      // bytes in D1 mode, bytes in one D2 stream
    reg clk = 0; always #5 clk = ~clk;
    reg host_tx = 1'b1; wire host_rx; wire [5:0] led_n; wire trig;
    lookup_board_top #(.CLK_HZ(CLK_HZ), .BAUD(BAUD), .POR_BITS(4), .TB(10), .CONF_HEX("../rtl/lookup/conf_lut.hex")) dut (
        .clk(clk), .btn_s1(1'b0), .btn_s2(1'b0), .uart_rx(host_tx), .uart_tx(host_rx), .led_n(led_n), .trig_out(trig));

    task send_byte(input [7:0] b);
        integer i;
        begin
            host_tx = 1'b0; repeat (CPB) @(posedge clk);
            for (i = 0; i < 8; i = i + 1) begin host_tx = b[i]; repeat (CPB) @(posedge clk); end
            host_tx = 1'b1; repeat (CPB) @(posedge clk);
        end
    endtask

    integer f, rx_n = 0, frame_err = 0;
    always begin : receiver
        integer i; reg [7:0] b;
        @(negedge host_rx);
        repeat (CPB / 2) @(posedge clk);
        if (host_rx !== 1'b0) frame_err = frame_err + 1;
        for (i = 0; i < 8; i = i + 1) begin repeat (CPB) @(posedge clk); b[i] = host_rx; end
        repeat (CPB) @(posedge clk);
        if (host_rx !== 1'b1) frame_err = frame_err + 1;
        $fwrite(f, "%02x\n", b); rx_n = rx_n + 1;
    end
    task wait_rx(input integer n);
        integer target, t;
        begin
            target = rx_n + n; t = 0;
            while (rx_n < target && t < 2000000) begin @(posedge clk); t = t + 1; end
            if (rx_n < target) begin $display("TIMEOUT waiting for %0d bytes", n); $finish; end
        end
    endtask

    reg [7:0] data [0:1023];
    integer i;
    initial begin
        $readmemh("in_board.hex", data);
        f = $fopen("rx_lookup.txt", "w");
        repeat (200) @(posedge clk);
        send_byte(8'hE0); wait_rx(1);
        for (i = 0; i < N1; i = i + 1) begin send_byte(8'hD1); send_byte(data[i]); wait_rx(4); end
        send_byte(8'hD2); send_byte(N2);
        fork
            begin for (i = 0; i < N2; i = i + 1) send_byte(data[N1 + i]); end
            wait_rx(N2 + 1);
        join
        send_byte(8'hF0); wait_rx(13);
        send_byte(8'hC2); send_byte(8'd20); send_byte(8'h77); wait_rx(1);
        send_byte(8'hD1); send_byte(data[N1 + N2]); wait_rx(4);
        send_byte(8'hB0); wait_rx(1);
        for (i = 0; i < 10; i = i + 1) begin send_byte(8'hD1); send_byte(data[i]); wait_rx(4); end
        send_byte(8'hF0); wait_rx(13);
        send_byte(8'hA1); wait_rx(1); send_byte(8'hA0); wait_rx(1);
        repeat (100) @(posedge clk);
        $fclose(f);
        $display("DONE rx=%0d frame_err=%0d trig=%0d", rx_n, frame_err, trig);
        $finish;
    end
endmodule
