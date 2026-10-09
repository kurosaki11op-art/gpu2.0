// uart_tx.v -- 8N1 UART transmitter (plain Verilog-2005, synthesizable).
// Pulse `send` for one clock with `data` while `busy` is low.
// `busy` stays high from the send pulse until the end of the stop bit.
module uart_tx #(
    parameter CLK_HZ = 27_000_000,
    parameter BAUD   = 115200
) (
    input       clk,
    input       rst,
    input       send,
    input [7:0] data,
    output reg  tx = 1'b1,     // idle high
    output      busy
);
    localparam integer CPB = CLK_HZ / BAUD;

    reg [15:0] cnt  = 16'd0;
    reg [3:0]  bitn = 4'd0;     // 0 start, 1..8 data, 9 stop
    reg [8:0]  sh   = 9'h1FF;
    reg        act  = 1'b0;
    assign busy = act;

    always @(posedge clk) begin
        if (rst) begin
            act <= 1'b0; tx <= 1'b1; cnt <= 16'd0; bitn <= 4'd0;
        end else if (!act) begin
            tx <= 1'b1;
            if (send) begin
                act  <= 1'b1;
                sh   <= {1'b1, data};   // stop bit, data[7:0]
                tx   <= 1'b0;           // start bit
                cnt  <= 16'd0;
                bitn <= 4'd0;
            end
        end else if (cnt == CPB - 1) begin
            cnt <= 16'd0;
            if (bitn == 4'd9) begin
                act <= 1'b0;            // stop bit done
                tx  <= 1'b1;
            end else begin
                tx   <= sh[0];
                sh   <= {1'b1, sh[8:1]};
                bitn <= bitn + 4'd1;
            end
        end else cnt <= cnt + 16'd1;
    end
endmodule
