// lookup_board_top.v -- SPARK-L v2 lookup core on the Sipeed Tang Nano 20K, driven over UART.
// Same ports as spark_board_top.v, so tangnano20k.cst works unchanged.
//
// Clock: 27 MHz crystal. Reset: power-on reset OR button S1 held. UART: 8N1, 115200 baud (onboard BL616 bridge).
//
// ---------------------------------------------------------------- protocol (host -> board)
//   E0            ping. Reply 5A (sent once the core has finished clearing its tables).
//   D1 b          predict after byte b. Reply 4 bytes: pred, flags, conf, chk
//                   flags: bit0 hit, bits3:1 src (0-3 hashed order 2/3/4/6, 4 order-1 table, 5 none), bits5:4 count
//                   chk = pred ^ flags ^ conf
//   D2 n b1..bn   stream n bytes (n = 1..255) back to back. Reply n bytes (the prediction after each), then chk = XOR of them.
//                   Input and reply run at the same baud rate; a 16-byte reply FIFO absorbs the small offset.
//   F0            read counters since the last clear. Reply 13 bytes: bytes[31:0], correct[31:0], hits[31:0] (little-endian), chk
//                   correct = bytes whose value equalled the prediction made just before them (the board scores itself)
//   C2 a v        write confidence-table entry a (0..31) = v. Reply C3.
//   B0            clear: reset the tables and counters (2^TB-cycle sweep). Reply B1 when done.
//   A0 / A1       benchmark marker pin low / high. Reply echo.
// The host must wait for each reply (for D2: the whole reply) before the next command.
//
// LEDs (active low): led[0] toggles per byte, led[1] core busy, led[2] marker, led[3] heartbeat,
// led[4] UART byte received (toggle), led[5] last prediction was a table hit.
module lookup_board_top #(
    parameter CLK_HZ   = 27_000_000,
    parameter BAUD     = 115200,
    parameter POR_BITS = 16,
    parameter TB       = 11,
    parameter CONF_HEX = "conf_lut.hex"
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

    // reply FIFO (16 bytes) and transmit pump
    reg [7:0] fifo [0:15];
    reg [3:0] wp = 4'd0, rp = 4'd0; reg [4:0] fcnt = 5'd0;
    reg       push = 1'b0; reg [7:0] push_d = 8'd0;
    reg       tx_wait = 1'b0;
    wire      pop = (fcnt != 5'd0) && !tx_busy && !tx_send && !tx_wait;
    always @(posedge clk) begin
        tx_send <= 1'b0; tx_wait <= 1'b0;
        if (rst) begin wp <= 4'd0; rp <= 4'd0; fcnt <= 5'd0; end
        else begin
            if (push) begin fifo[wp] <= push_d; wp <= wp + 4'd1; end
            if (pop)  begin tx_data <= fifo[rp]; tx_send <= 1'b1; tx_wait <= 1'b1; rp <= rp + 4'd1; end
            fcnt <= fcnt + (push ? 5'd1 : 5'd0) - (pop ? 5'd1 : 5'd0);
        end
    end

    // ------------------------------------------------------------ core
    reg        core_clr = 1'b0;
    reg        in_valid = 1'b0; reg [7:0] in_byte = 8'd0;
    reg        cfg_we = 1'b0; reg [4:0] cfg_addr = 5'd0; reg [7:0] cfg_data = 8'd0;
    wire       busy, out_valid, hit; wire [7:0] pred, conf; wire [2:0] src; wire [1:0] count; wire [4:0] bucket;
    spark_lookup2 #(.TB(TB), .CONF_HEX(CONF_HEX)) u_core (
        .clk(clk), .rst(rst | core_clr), .in_valid(in_valid), .in_byte(in_byte),
        .cfg_we(cfg_we), .cfg_addr(cfg_addr), .cfg_data(cfg_data),
        .busy(busy), .out_valid(out_valid), .pred(pred), .hit(hit), .src(src), .count(count), .bucket(bucket), .conf(conf));

    // ------------------------------------------------------------ command FSM
    localparam S_CMD = 4'd0, S_D1 = 4'd1, S_D2N = 4'd2, S_D2B = 4'd3, S_RUN = 4'd4, S_WAITC = 4'd5,
               S_C2A = 4'd6, S_C2V = 4'd7, S_CLR = 4'd8, S_REPLY = 4'd9, S_PING = 4'd10, S_D2END = 4'd11;
    reg [3:0]  state = S_CMD;
    reg        mode2 = 1'b0;                 // 0: D1 (4-byte reply), 1: D2 stream
    reg [7:0]  left = 8'd0, xacc = 8'd0;
    reg [31:0] n_bytes = 32'd0, n_correct = 32'd0, n_hits = 32'd0;
    reg [7:0]  last_pred = 8'd0; reg have_pred = 1'b0;
    reg [7:0]  rbuf [0:12]; reg [3:0] rlen = 4'd0, ri = 4'd0;
    reg        marker = 1'b0, byte_led = 1'b0, rx_led = 1'b0, hit_led = 1'b0;
    reg [7:0]  pend; reg pend_v = 1'b0;     // stream byte waiting for the core

    wire [7:0] flags = {2'b00, count, src, hit};

    always @(posedge clk) begin
        in_valid <= 1'b0; cfg_we <= 1'b0; core_clr <= 1'b0; push <= 1'b0;
        if (rx_valid) rx_led <= ~rx_led;
        if (rst) begin
            state <= S_CMD; n_bytes <= 0; n_correct <= 0; n_hits <= 0; have_pred <= 1'b0; pend_v <= 1'b0;
        end else begin
            // a stream byte that arrives while the previous one is still in the core waits in `pend`
            if (state == S_D2B && rx_valid) begin pend <= rx_data; pend_v <= 1'b1; end
            case (state)
            S_CMD: if (rx_valid) case (rx_data)
                8'hE0: state <= S_PING;
                8'hD1: begin mode2 <= 1'b0; state <= S_D1; end
                8'hD2: begin mode2 <= 1'b1; state <= S_D2N; end
                8'hF0: begin
                    rbuf[0] <= n_bytes[7:0];   rbuf[1] <= n_bytes[15:8];   rbuf[2]  <= n_bytes[23:16];   rbuf[3]  <= n_bytes[31:24];
                    rbuf[4] <= n_correct[7:0]; rbuf[5] <= n_correct[15:8]; rbuf[6]  <= n_correct[23:16]; rbuf[7]  <= n_correct[31:24];
                    rbuf[8] <= n_hits[7:0];    rbuf[9] <= n_hits[15:8];    rbuf[10] <= n_hits[23:16];    rbuf[11] <= n_hits[31:24];
                    rbuf[12] <= n_bytes[7:0] ^ n_bytes[15:8] ^ n_bytes[23:16] ^ n_bytes[31:24]
                              ^ n_correct[7:0] ^ n_correct[15:8] ^ n_correct[23:16] ^ n_correct[31:24]
                              ^ n_hits[7:0] ^ n_hits[15:8] ^ n_hits[23:16] ^ n_hits[31:24];
                    rlen <= 4'd13; ri <= 4'd0; state <= S_REPLY;
                end
                8'hC2: state <= S_C2A;
                8'hB0: begin core_clr <= 1'b1; n_bytes <= 0; n_correct <= 0; n_hits <= 0; have_pred <= 1'b0; state <= S_CLR; end
                8'hA0, 8'hA1: begin marker <= rx_data[0]; rbuf[0] <= rx_data; rlen <= 4'd1; ri <= 4'd0; state <= S_REPLY; end
                default: ;
            endcase
            S_PING: if (!busy) begin rbuf[0] <= 8'h5A; rlen <= 4'd1; ri <= 4'd0; state <= S_REPLY; end
            S_D1: if (rx_valid) begin pend <= rx_data; pend_v <= 1'b1; state <= S_RUN; end
            S_D2N: if (rx_valid) begin left <= rx_data; xacc <= 8'd0; state <= (rx_data == 8'd0) ? S_D2END : S_D2B; end
            S_D2B: if (pend_v && !busy) state <= S_RUN;
            S_RUN: if (!busy) begin                     // score the arriving byte against the previous prediction, then feed it
                in_byte <= pend; in_valid <= 1'b1; pend_v <= 1'b0;
                if (have_pred && last_pred == pend) n_correct <= n_correct + 32'd1;
                state <= S_WAITC;
            end
            S_WAITC: if (out_valid) begin
                n_bytes <= n_bytes + 32'd1; n_hits <= n_hits + {31'd0, hit};
                last_pred <= pred; have_pred <= 1'b1; byte_led <= ~byte_led; hit_led <= hit;
                if (!mode2) begin
                    rbuf[0] <= pred; rbuf[1] <= flags; rbuf[2] <= conf; rbuf[3] <= pred ^ flags ^ conf;
                    rlen <= 4'd4; ri <= 4'd0; state <= S_REPLY;
                end else begin
                    push <= 1'b1; push_d <= pred; xacc <= xacc ^ pred;
                    left <= left - 8'd1;
                    state <= (left == 8'd1) ? S_D2END : S_D2B;
                end
            end
            S_D2END: begin push <= 1'b1; push_d <= xacc; state <= S_CMD; end
            S_C2A: if (rx_valid) begin cfg_addr <= rx_data[4:0]; state <= S_C2V; end
            S_C2V: if (rx_valid) begin cfg_data <= rx_data; cfg_we <= 1'b1; rbuf[0] <= 8'hC3; rlen <= 4'd1; ri <= 4'd0; state <= S_REPLY; end
            S_CLR: if (!core_clr && !busy) begin rbuf[0] <= 8'hB1; rlen <= 4'd1; ri <= 4'd0; state <= S_REPLY; end
            S_REPLY: if (fcnt < 5'd15) begin          // copy the reply buffer into the FIFO, one byte per cycle
                push <= 1'b1; push_d <= rbuf[ri]; ri <= ri + 4'd1;
                if (ri + 4'd1 == rlen) state <= S_CMD;
            end
            default: state <= S_CMD;
            endcase
        end
    end

    // ------------------------------------------------------------ LEDs
    reg [24:0] hb = 25'd0;
    always @(posedge clk) hb <= hb + 1'b1;
    assign led_n    = ~{hit_led, rx_led, hb[24], marker, busy, byte_led};
    assign trig_out = marker;
endmodule
