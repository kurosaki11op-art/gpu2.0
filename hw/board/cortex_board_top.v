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
//   54 + 128 x 4 bytes      load the 128 sensory detectors (channel-major, 32 per channel; 25 bits little-endian,
//                           bit r*5+c = window row r, column c). Reply 54.
//   49 c + 784 bytes        IMAGE: the chip encodes the 28x28 image itself (cortex_encoder.v), then LEARNs it as class c
//                           (reply: updated) or, with c = FF, PREDICTs (reply: class).
// Memory transfer (export / import what the chip knows; one word per code bit b = 0..4607):
//   52 bl bh                read word b. Reply 20 bytes: table word (50 bits in 7 bytes) then counts (100 bits in 13).
//   57 bl bh + 20 bytes     write word b (same layout). Reply 57.
//   4E                      read the example counts (10 x 10 bits in 13 bytes) and the known classes (2 bytes). Reply 15 bytes.
//   4D + 15 bytes           write them (same layout). Reply 4D.
// The host runs the day/night schedule (cortex_host.py) and ends a night itself from the `updated` replies.
//
// LEDs (active low): led[0] toggles per command, led[1] core busy, led[2] last LEARN/DREAM wrote the table,
// led[3] heartbeat, led[4] UART byte received (toggle), led[5] last prediction was class 0..4 (on) or 5..9 (off).
module cortex_board_top #(
    parameter CLK_HZ   = 27_000_000,
`ifdef FAST_UART
    parameter BAUD     = 921600,           // optional fast build (define FAST_UART); only if the USB bridge supports it
`else
    parameter BAUD     = 115200,
`endif
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
    reg [7:0] rbuf [0:19]; reg [4:0] rlen = 0, ri = 0; reg sending = 1'b0; reg start_reply = 1'b0;
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
    reg [AW-1:0] mem_addr = 0; reg [159:0] wbuf = 0;
    wire [49:0] rd_w; wire [99:0] rd_c, rd_n; wire [9:0] rd_known;
    // sensory encoder: writes its list of active code bits through the core's list port
    reg pix_we = 1'b0; reg [9:0] pix_addr = 0; reg [7:0] pix_data = 0;
    reg tm_we = 1'b0; reg [1:0] tm_ch = 0; reg [4:0] tm_f = 0; reg [24:0] tm_data = 0; reg enc_start = 1'b0;
    wire enc_busy, enc_done, enc_we; wire [AW:0] enc_count; wire [AW-1:0] enc_addr, enc_data;
    cortex_encoder #(.AW(AW)) u_enc (.clk(clk), .rst(rst), .pix_we(pix_we), .pix_addr(pix_addr), .pix_data(pix_data),
        .tm_we(tm_we), .tm_ch(tm_ch), .tm_f(tm_f), .tm_data(tm_data), .start(enc_start),
        .busy(enc_busy), .done(enc_done), .count(enc_count), .out_we(enc_we), .out_addr(enc_addr), .out_data(enc_data));
    cortex_core #(.NB(NB), .AW(AW)) u_core (.clk(clk), .rst(rst), .cmd_valid(cmd_valid), .cmd_op(cmd_op), .cmd_arg(cmd_arg),
        .lb_we(lb_we | enc_we), .lb_waddr(enc_we ? enc_addr : lb_waddr), .lb_wdata(enc_we ? enc_data : lb_wdata), .lb_len(lb_len),
        .lane_we(lane_we), .lane_waddr(lane_waddr), .lane_wdata(lane_wdata),
        .mem_addr(mem_addr), .wr_w(op == 8'h4D ? {40'd0, wbuf[113:104]} : wbuf[49:0]), .wr_c(op == 8'h4D ? wbuf[99:0] : wbuf[155:56]),
        .busy(busy), .pred(pred), .updated(updated), .llen_out(llen_out),
        .rd_w(rd_w), .rd_c(rd_c), .rd_n(rd_n), .rd_known(rd_known));
    wire [159:0] rdv = {4'd0, rd_c, 6'd0, rd_w};
    wire [119:0] rnv = {6'd0, rd_known, 4'd0, rd_n};

    // ------------------------------------------------------------ command FSM
    localparam S_CMD = 0, S_ARG = 1, S_NL = 2, S_NH = 3, S_IL = 4, S_IH = 5, S_GO = 6, S_WAIT = 7, S_SEED = 8, S_REP = 9,
               S_TM = 10, S_IARG = 11, S_PIX = 12, S_ENC = 13, S_AL = 14, S_AH = 15, S_WB = 16, S_WS = 17;
    reg [4:0] state = S_CMD; reg [4:0] wcnt = 0; reg [7:0] op = 0; reg [AW:0] cnt = 0; reg [7:0] lo = 0;
    reg [8:0] tidx = 0; reg [23:0] tacc = 0; reg [9:0] pcnt = 0; reg enc_wait = 1'b0;
    reg [6:0] sidx = 0; reg [31:0] sw = 0; reg wrote = 1'b0, lowcls = 1'b0, cmd_led = 1'b0, rx_led = 1'b0;
    reg go_wait = 1'b0; integer j;
    always @(posedge clk) begin
        cmd_valid <= 1'b0; lb_we <= 1'b0; lane_we <= 1'b0; start_reply <= 1'b0; pix_we <= 1'b0; tm_we <= 1'b0; enc_start <= 1'b0;
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
                8'h54: begin tidx <= 0; state <= S_TM; end
                8'h49: state <= S_IARG;
                8'h52, 8'h57: state <= S_AL;
                8'h4E: begin cmd_op <= 3'd7; cmd_arg <= 4'd3; state <= S_GO; end          // arg 3: no-op, just reply counts
                8'h4D: begin wcnt <= 0; state <= S_WB; end
                default: ;
            endcase
        end
        S_SEED: if (rx_valid) begin
            sw <= {rx_data, sw[31:8]};
            if (sidx[1:0] == 2'd3) begin lane_we <= 1'b1; lane_waddr <= sidx[6:2]; lane_wdata <= {rx_data, sw[31:8]}; end
            sidx <= sidx + 1'b1;
            if (sidx == 7'd127) begin rbuf[0] <= 8'h53; rlen <= 1; state <= S_REP; end
        end
        S_TM: if (rx_valid) begin                              // detectors: 4 bytes each, little-endian
            tacc <= {rx_data, tacc[23:8]};
            if (tidx[1:0] == 2'd3) begin tm_we <= 1'b1; tm_ch <= tidx[8:7]; tm_f <= tidx[6:2]; tm_data <= {rx_data[0], tacc}; end
            tidx <= tidx + 1'b1;
            if (tidx == 9'd511) begin rbuf[0] <= 8'h54; rlen <= 1; state <= S_REP; end
        end
        S_IARG: if (rx_valid) begin
            if (rx_data == 8'hFF) begin cmd_op <= 3'd4; cmd_arg <= 0; op <= 8'h50; end
            else begin cmd_op <= 3'd1; cmd_arg <= rx_data[3:0]; op <= 8'h4C; end
            pcnt <= 0; state <= S_PIX;
        end
        S_PIX: if (rx_valid) begin
            pix_we <= 1'b1; pix_addr <= pcnt; pix_data <= rx_data; pcnt <= pcnt + 1'b1;
            if (pcnt == 10'd783) begin enc_wait <= 1'b1; state <= S_ENC; end
        end
        S_ENC: if (enc_wait) begin if (!pix_we) begin enc_start <= 1'b1; enc_wait <= 1'b0; end end
               else if (enc_done) begin lb_len <= enc_count; state <= S_GO; end
        S_AL: if (rx_valid) begin mem_addr[7:0] <= rx_data; state <= S_AH; end
        S_AH: if (rx_valid) begin
            mem_addr[AW-1:8] <= rx_data[AW-9:0]; cmd_op <= 3'd7;
            if (op == 8'h52) begin cmd_arg <= 4'd0; state <= S_GO; end else begin wcnt <= 0; state <= S_WB; end
        end
        S_WB: if (rx_valid) begin                          // collect 20 (57) or 15 (4D) bytes, little-endian
            wbuf <= {rx_data, wbuf[159:8]}; wcnt <= wcnt + 1'b1;
            if (op == 8'h57 && wcnt == 5'd19) begin cmd_arg <= 4'd1; state <= S_GO; end
            if (op == 8'h4D && wcnt == 5'd14) begin cmd_op <= 3'd7; cmd_arg <= 4'd2; state <= S_WS; end
        end
        S_WS: begin wbuf <= wbuf >> 40; state <= S_GO; end           // 15 bytes arrived at the top: shift them down
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
                8'h52: begin for (j = 0; j < 20; j = j + 1) rbuf[j] <= rdv[j*8 +: 8]; rlen <= 20; end
                8'h4E: begin for (j = 0; j < 15; j = j + 1) rbuf[j] <= rnv[j*8 +: 8]; rlen <= 15; end
                8'h57: begin rbuf[0] <= 8'h57; rlen <= 1; end
                8'h4D: begin rbuf[0] <= 8'h4D; rlen <= 1; end
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
