// Wrapper used only for resource counting: one UART receiver and one transmitter, as in the board top.
module uart_pair (input clk, input rst, input rx, input send, input [7:0] din, output tx, output [7:0] dout, output valid, output busy);
    uart_rx u_rx (.clk(clk), .rst(rst), .rx(rx), .data(dout), .valid(valid));
    uart_tx u_tx (.clk(clk), .rst(rst), .send(send), .data(din), .tx(tx), .busy(busy));
endmodule
