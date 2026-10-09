// uart_rx.v -- 8N1 UART receiver (plain Verilog-2005, synthesizable).
// CLKS_PER_BIT = CLK_HZ / BAUD (27 MHz / 115200 = 234, 0.16 % error).
// `valid` pulses for one clock with the received byte in `data`.
// A frame with a bad stop bit is dropped (no valid pulse).
module uart_rx #(
    parameter CLK_HZ = 27_000_000,
    parameter BAUD   = 115200
) (
    input            clk,
    input            rst,
    input            rx,          // idle high
    output reg [7:0] data,
    output reg       valid
);
    localparam integer CPB  = CLK_HZ / BAUD;
    localparam integer HALF = CPB / 2;

    // two-flop synchroniser (rx is asynchronous to clk)
    reg rx_m = 1'b1, rx_s = 1'b1;
    always @(posedge clk) begin
        rx_m <= rx;
        rx_s <= rx_m;
    end

    localparam S_IDLE = 2'd0, S_START = 2'd1, S_DATA = 2'd2, S_STOP = 2'd3;
    reg [1:0]  state = S_IDLE;
    reg [15:0] cnt   = 16'd0;
    reg [2:0]  bitn  = 3'd0;
    reg [7:0]  sh    = 8'd0;

    always @(posedge clk) begin
        valid <= 1'b0;
        if (rst) begin
            state <= S_IDLE; cnt <= 16'd0; bitn <= 3'd0;
        end else begin
            case (state)
            S_IDLE:
                if (!rx_s) begin state <= S_START; cnt <= 16'd0; end
            S_START:                         // re-check start bit at its middle
                if (cnt == HALF - 1) begin
                    cnt <= 16'd0;
                    if (!rx_s) begin state <= S_DATA; bitn <= 3'd0; end
                    else state <= S_IDLE;    // glitch
                end else cnt <= cnt + 16'd1;
            S_DATA:
                if (cnt == CPB - 1) begin
                    cnt <= 16'd0;
                    sh  <= {rx_s, sh[7:1]};  // LSB first
                    if (bitn == 3'd7) state <= S_STOP;
                    bitn <= bitn + 3'd1;
                end else cnt <= cnt + 16'd1;
            S_STOP:
                if (cnt == CPB - 1) begin
                    cnt <= 16'd0;
                    state <= S_IDLE;
                    if (rx_s) begin data <= sh; valid <= 1'b1; end
                end else cnt <= cnt + 16'd1;
            endcase
        end
    end
endmodule
