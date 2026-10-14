// cortex_board_top.v -- SPARK Cortex core on the Sipeed Tang Nano 20K, driven over UART.
// Same ports as spark_board_top.v / lookup_board_top.v, so tangnano20k.cst works unchanged.
//
// Clock: 27 MHz crystal. Reset: power-on reset OR button S1 held (the host should then send CLEAR).
// UART: 8N1, BAUD (default 115200) through the onboard USB bridge.
//
// ---------------------------------------------------------------- protocol (host -> board), one command at a time
//   E0                      ping. Reply 5A.
//   53 s0..s127             seed the 32 random lanes (32 x 4 bytes, little-endian). Reply 53.
//   43                      CLEAR table, dream counters, counts, known classes. Reply 43 when done.
//   4B c                    mark class c known. Reply 4B.
//   4C c nl nh i0l i0h ...  LEARN: n = nh:nl active code bits (2 bytes each, little-endian) of an example of class c.
//                           Reply: updated (1 if the table was written).
//   50 nl nh i0l i0h ...    PREDICT on the listed code bits. Reply: predicted class.
//   44 c                    DREAM a class-c example and practise on it. Reply: dream length low, high, updated.
// The host runs the day/night schedule (cortex_host.py) and ends a night itself from the `updated` replies.
//
// LEDs (active low): led[0] toggles per command, led[1] core busy, led[2] last LEARN/DREAM wrote the table,
// led[3] heartbeat, led[4] UART byte received (toggle), led[5] last prediction was class 0..4 (on) or 5..9 (off).
module cortex_board_top #(
    parameter CLK_HZ   = 27_000_000,
    parameter BAUD     = 115200,
    parameter POR_BITS = 16,
    parameter NB       = 4608,
    parameter AW       = 13
) (
    input        clk,
    input        btn_s1,
    input        btn_s2,
    input        uart_rx,
    output       uart_tx,
    output [5:0] led_n,
    output       trig_out
);
    // ------------------------------------------------------------ reset
    reg [POR_BITS:0] por = 0;
    always @(posedge clk) if (!por[POR_BITS]) por <= por + 1'b1;
    reg btn_m = 1'b0, btn_s = 1'b0;
    always @(posedge clk) begin btn_m <= btn_s1; btn_s <= btn_m; end
    reg rst = 1'b1;
    always @(posedge clk) rst <= ~por[POR_BITS] | btn_s;

    // ------------------------------------------------------------ UART
    wire [7:0] rx_data; wire rx_valid;
    reg  [7:0] tx_data = 8'd0; reg tx_send = 1'b0; wire tx_busy;
    uart_rx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) u_rx (.clk(clk), .rst(rst), .rx(uart_rx), .data(rx_data), .valid(rx_valid));
    uart_tx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) u_tx (.clk(clk), .rst(rst), .send(tx_send), .data(tx_data), .tx(uart_tx), .busy(tx_busy));
    reg [7:0] rbuf [0:2]; reg [2:0] rlen = 0, ri = 0; reg sending = 1'b0; reg start_reply = 1'b0;
    always @(posedge clk) begin
        tx_send <= 1'b0;
        if (rst) begin sending <= 1'b0; ri <= 0; end
        else if (sending && !tx_busy && !tx_send) begin
            if (ri == rlen) sending <= 1'b0;
            else begin tx_data <= rbuf[ri]; tx_send <= 1'b1; ri <= ri + 1'b1; end
        end else if (start_reply) begin sending <= 1'b1; ri <= 0; end
    end

    // ------------------------------------------------------------ core
    reg cmd_valid = 1'b0; reg [2:0] cmd_op = 0; reg [3:0] cmd_arg = 0;
    reg lb_we = 1'b0; reg [AW-1:0] lb_waddr = 0, lb_wdata = 0; reg [AW:0] lb_len = 0;
    reg lane_we = 1'b0; reg [4:0] lane_waddr = 0; reg [31:0] lane_wdata = 0;
    wire busy, updated; wire [3:0] pred; wire [AW:0] llen_out;
    cortex_core #(.NB(NB), .AW(AW)) u_core (.clk(clk), .rst(rst), .cmd_valid(cmd_valid), .cmd_op(cmd_op), .cmd_arg(cmd_arg),
        .lb_we(lb_we), .lb_waddr(lb_waddr), .lb_wdata(lb_wdata), .lb_len(lb_len),
        .lane_we(lane_we), .lane_waddr(lane_waddr), .lane_wdata(lane_wdata),
        .busy(busy), .pred(pred), .updated(updated), .llen_out(llen_out));

    // ------------------------------------------------------------ command FSM
    localparam S_CMD = 0, S_ARG = 1, S_NL = 2, S_NH = 3, S_IL = 4, S_IH = 5, S_GO = 6, S_WAIT = 7, S_SEED = 8, S_REP = 9;
    reg [3:0] state = S_CMD; reg [7:0] op = 0; reg [AW:0] cnt = 0; reg [7:0] lo = 0;
    reg [6:0] sidx = 0; reg [31:0] sw = 0; reg wrote = 1'b0, lowcls = 1'b0, cmd_led = 1'b0, rx_led = 1'b0;
    reg go_wait = 1'b0;
    always @(posedge clk) begin
        cmd_valid <= 1'b0; lb_we <= 1'b0; lane_we <= 1'b0; start_reply <= 1'b0;
        if (rx_valid) rx_led <= ~rx_led;
        if (rst) state <= S_CMD;
        else case (state)
        S_CMD: if (rx_valid && !sending) begin
            op <= rx_data; cmd_led <= ~cmd_led;
            case (rx_data)
                8'hE0: begin rbuf[0] <= 8'h5A; rlen <= 1; state <= S_REP; end
                8'h53: begin sidx <= 0; state <= S_SEED; end
                8'h43: begin cmd_op <= 3'd6; state <= S_GO; end
                8'h4B, 8'h44, 8'h4C: state <= S_ARG;
                8'h50: begin cmd_op <= 3'd4; cmd_arg <= 0; state <= S_NL; end
                default: ;
            endcase
        end
        S_SEED: if (rx_valid) begin
            sw <= {rx_data, sw[31:8]};
            if (sidx[1:0] == 2'd3) begin lane_we <= 1'b1; lane_waddr <= sidx[6:2]; lane_wdata <= {rx_data, sw[31:8]}; end
            sidx <= sidx + 1'b1;
            if (sidx == 7'd127) begin rbuf[0] <= 8'h53; rlen <= 1; state <= S_REP; end
        end
        S_ARG: if (rx_valid) begin
            cmd_arg <= rx_data[3:0];
            if (op == 8'h4B) begin cmd_op <= 3'd5; state <= S_GO; end
            else if (op == 8'h44) begin cmd_op <= 3'd3; state <= S_GO; end
            else begin cmd_op <= 3'd1; state <= S_NL; end
        end
        S_NL: if (rx_valid) begin lb_len[7:0] <= rx_data; state <= S_NH; end
        S_NH: if (rx_valid) begin
            lb_len[AW:8] <= rx_data[AW-8:0]; cnt <= 0;
            state <= ({rx_data[AW-8:0], lb_len[7:0]} == 0) ? S_GO : S_IL;
        end
        S_IL: if (rx_valid) begin lo <= rx_data; state <= S_IH; end
        S_IH: if (rx_valid) begin
            lb_we <= 1'b1; lb_waddr <= cnt[AW-1:0]; lb_wdata <= {rx_data[AW-8-1:0], lo};
            cnt <= cnt + 1'b1; state <= (cnt + 1'b1 == lb_len) ? S_GO : S_IL;
        end
        S_GO: if (!busy) begin cmd_valid <= 1'b1; go_wait <= 1'b1; state <= S_WAIT; end
        S_WAIT: if (go_wait) go_wait <= 1'b0;                 // core raises busy the cycle after cmd_valid
                else if (!busy && !cmd_valid) begin
            case (op)
                8'h43: begin rbuf[0] <= 8'h43; rlen <= 1; end
                8'h4B: begin rbuf[0] <= 8'h4B; rlen <= 1; end
                8'h4C: begin rbuf[0] <= {7'd0, updated}; rlen <= 1; wrote <= updated; end
                8'h50: begin rbuf[0] <= {4'd0, pred}; rlen <= 1; lowcls <= (pred < 4'd5); end
                8'h44: begin rbuf[0] <= llen_out[7:0]; rbuf[1] <= {{(15-AW){1'b0}}, llen_out[AW:8]}; rbuf[2] <= {7'd0, updated};
                             rlen <= 3; wrote <= updated; end
                default: rlen <= 0;
            endcase
            state <= S_REP;
        end
        S_REP: begin start_reply <= 1'b1; state <= S_CMD; end
        default: state <= S_CMD;
        endcase
    end

    // ------------------------------------------------------------ LEDs
    reg [24:0] hb = 25'd0;
    always @(posedge clk) hb <= hb + 1'b1;
    assign led_n    = ~{lowcls, rx_led, hb[24], wrote, busy, cmd_led};
    assign trig_out = busy;
endmodule
