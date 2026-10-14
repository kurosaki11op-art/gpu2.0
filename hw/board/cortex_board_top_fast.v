// Optional fast-UART top (921,600 baud): the same design as cortex_board_top with only BAUD changed. Same ports, so
// tangnano20k.cst applies. Use it only if the board's USB bridge answers at this rate.
module cortex_board_top_fast (
    input clk, input btn_s1, input btn_s2, input uart_rx, output uart_tx, output [5:0] led_n, output trig_out
);
    cortex_board_top #(.BAUD(921600)) u (.clk(clk), .btn_s1(btn_s1), .btn_s2(btn_s2), .uart_rx(uart_rx),
        .uart_tx(uart_tx), .led_n(led_n), .trig_out(trig_out));
endmodule
