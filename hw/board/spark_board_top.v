// spark_board_top.v -- SPARK core on the Sipeed Tang Nano 20K, driven over UART.
//
// Clock: 27 MHz crystal. Reset: power-on reset (~2.4 ms) OR button S1 held.
// UART: 8N1, 115200 baud by default (onboard BL616 USB-UART bridge).
//
// ---------------------------------------------------------------- protocol
// Host -> FPGA command bytes (anything else is ignored while idle):
//   0xC0 c0..c7   set config (8 bytes follow):
//                   c0 flags: bit0 sparse_en, bit1 delta_en, bit2 exit_en,
//                             bit3 recall_en, bit4 adapt_en, bit5 thr_en
//                             (thr_en = threshold spikes; must be 1 for models
//                              that have per-neuron thresholds, i.e. th0/th1)
//                   c1 cap[7:0], c2 cap[15:8]       (0 = no energy cap)
//                   c3..c6 exit_th[31:0], little-endian, two's complement
//                   c7 bits [1:0] conf_th, [3:2] recall_mode (0 bypass network,
//                      1 fresh state, 2 arbitration), [7:4] arb_th/16 (mode 2)
//                 reply: 0xC1 (ack)
//   0xD0 b        run one token (input byte b) through spark_core.
//                 reply (7 bytes): pred, path, cyc[7:0], cyc[15:8], cyc[23:16],
//                 cyc[31:24], chk     where cyc = tok_cycles (clock cycles in
//                 the core for this token) and chk = XOR of the first 6 bytes.
//   0xE0          ping, reply 0x5A.
//   0xA0 / 0xA1   drive the benchmark marker pin (trig_out) low / high
//                 (for the ESP32 INA219 logger). reply: 0xA0 / 0xA1 (echo).
// Power-on config: sparse_en=1, everything else off, cap=0, exit_th=64, conf_th=1.
// The host must wait for each reply before sending the next command; bytes that
// arrive while a token is running or a reply is being sent are dropped.
// Core state (context, recall table, accumulators in BRAM) persists across
// tokens and config changes; only a bitstream reload clears the BRAM state.
//
// LEDs (active low on the board): led[0] toggles on every token, led[1] = core
// busy (token running), led[2] = marker pin state, led[3] = heartbeat,
// led[4] = UART byte received (toggle), led[5] = config received (toggle).
module spark_board_top #(
    parameter CLK_HZ  = 27_000_000,
    parameter BAUD    = 115200,
    parameter POR_BITS = 16,              // 2^16 / 27 MHz ~ 2.4 ms
    parameter EMB_HEX = "emb.hex",
    parameter W0_HEX  = "w0.hex",
    parameter W1_HEX  = "w1.hex",
    parameter W2_HEX  = "w2.hex",
    parameter W3_HEX  = "w3.hex",
    parameter EMB1_HEX = "emb1.hex",
    parameter EMB2_HEX = "emb2.hex",
    parameter TH0_HEX  = "th0.hex",
    parameter TH1_HEX  = "th1.hex",
    parameter THR_DEFAULT = 1'b1           // power-on spike mode (1 = threshold spikes)
) (
    input        clk,            // 27 MHz
    input        btn_s1,         // reset button (active high when pressed; see .cst TODO)
    input        btn_s2,         // unused (reserved)
    input        uart_rx,        // from BL616 (host TX)
    output       uart_tx,        // to BL616 (host RX)
    output [5:0] led_n,          // active low
    output       trig_out        // benchmark marker for the ESP32 logger
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
    uart_rx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) u_rx (
        .clk(clk), .rst(rst), .rx(uart_rx), .data(rx_data), .valid(rx_valid));
    uart_tx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) u_tx (
        .clk(clk), .rst(rst), .send(tx_send), .data(tx_data), .tx(uart_tx), .busy(tx_busy));

    // ------------------------------------------------------------ config
    reg        sparse_en = 1'b1, delta_en = 1'b0, exit_en = 1'b0, recall_en = 1'b0, adapt_en = 1'b0;
    reg        thr_en = THR_DEFAULT;
    reg [15:0] cap = 16'd0;
    reg [31:0] exit_th = 32'd64;
    reg [1:0]  conf_th = 2'd1;
    reg [1:0]  recall_mode = 2'd0;
    reg [15:0] arb_th = 16'd64;

    // ------------------------------------------------------------ core
    reg        start = 1'b0;
    reg  [7:0] in_byte = 8'd0;
    wire       done;
    wire [7:0] pred; wire [1:0] path; wire [31:0] tok_cycles;
    wire [31:0] wreads, ce, cs, cp, cr;
    wire [15:0] a0, a1, a2, a3, b0, b1, b2, b3;
    spark_core #(.EMB_HEX(EMB_HEX), .W0_HEX(W0_HEX), .W1_HEX(W1_HEX),
                 .W2_HEX(W2_HEX), .W3_HEX(W3_HEX), .EMB1_HEX(EMB1_HEX), .EMB2_HEX(EMB2_HEX),
                 .TH0_HEX(TH0_HEX), .TH1_HEX(TH1_HEX)) u_core (
        .clk(clk), .rst(rst), .start(start), .in_byte(in_byte),
        .sparse_en(sparse_en), .delta_en(delta_en), .exit_en(exit_en), .recall_en(recall_en),
        .cap(cap), .recall_mode(recall_mode), .arb_th(arb_th), .exit_th(exit_th), .conf_th(conf_th),
        .cfg_a(9'd230), .acc_sh(4'd2), .s_sh(4'd4), .adapt_en(adapt_en), .thr_en(thr_en),
        .ld_we(1'b0), .ld_sel(3'd0), .ld_addr(11'd0), .ld_data(64'd0),
        .done(done), .pred(pred), .path(path), .tok_cycles(tok_cycles), .wreads(wreads),
        .cyc_engine(ce), .cyc_scan(cs), .cyc_post(cp), .cyc_recall(cr),
        .nz0(a0), .nz1(a1), .nz2(a2), .nz3(a3), .pr0(b0), .pr1(b1), .pr2(b2), .pr3(b3)
    );

    // ------------------------------------------------------------ command FSM
    localparam S_CMD = 3'd0, S_CFG = 3'd1, S_DATA = 3'd2, S_RUN = 3'd3, S_WAIT = 3'd4, S_TX = 3'd5;
    reg [2:0]  state = S_CMD;
    reg [3:0]  cnt = 4'd0;            // config byte index / reply byte index
    reg [3:0]  rlen = 4'd0;           // reply length
    reg [7:0]  cfgb [0:7];
    reg [7:0]  rbuf [0:6];
    reg        marker = 1'b0, tok_led = 1'b0, rx_led = 1'b0, cfg_led = 1'b0;
    reg        tx_wait = 1'b0;        // one-cycle guard: busy rises the cycle after send
    wire [7:0] chk = pred ^ {6'd0, path} ^ tok_cycles[7:0] ^ tok_cycles[15:8]
                   ^ tok_cycles[23:16] ^ tok_cycles[31:24];

    always @(posedge clk) begin
        start   <= 1'b0;
        tx_send <= 1'b0;
        tx_wait <= 1'b0;
        if (rx_valid) rx_led <= ~rx_led;
        if (rst) begin
            state <= S_CMD; cnt <= 4'd0;
        end else case (state)
        S_CMD: if (rx_valid) begin
            case (rx_data)
            8'hC0: begin state <= S_CFG; cnt <= 4'd0; end
            8'hD0: state <= S_DATA;
            8'hE0: begin rbuf[0] <= 8'h5A; rlen <= 4'd1; cnt <= 4'd0; state <= S_TX; end
            8'hA0, 8'hA1: begin
                marker <= rx_data[0];
                rbuf[0] <= rx_data; rlen <= 4'd1; cnt <= 4'd0; state <= S_TX;
            end
            default: ;
            endcase
        end
        S_CFG: if (rx_valid) begin
            cfgb[cnt[2:0]] <= rx_data;
            cnt <= cnt + 4'd1;
            if (cnt == 4'd7) begin
                sparse_en <= cfgb[0][0]; delta_en <= cfgb[0][1]; exit_en <= cfgb[0][2];
                recall_en <= cfgb[0][3]; adapt_en <= cfgb[0][4]; thr_en <= cfgb[0][5];
                cap       <= {cfgb[2], cfgb[1]};
                exit_th   <= {cfgb[6], cfgb[5], cfgb[4], cfgb[3]};
                conf_th   <= rx_data[1:0];
                recall_mode <= rx_data[3:2];
                arb_th    <= {8'd0, rx_data[7:4], 4'd0};
                cfg_led   <= ~cfg_led;
                rbuf[0] <= 8'hC1; rlen <= 4'd1; cnt <= 4'd0; state <= S_TX;
            end
        end
        S_DATA: if (rx_valid) begin
            in_byte <= rx_data; state <= S_RUN;
        end
        S_RUN: begin start <= 1'b1; state <= S_WAIT; end
        S_WAIT: if (done) begin
            tok_led <= ~tok_led;
            rbuf[0] <= pred; rbuf[1] <= {6'd0, path};
            rbuf[2] <= tok_cycles[7:0];   rbuf[3] <= tok_cycles[15:8];
            rbuf[4] <= tok_cycles[23:16]; rbuf[5] <= tok_cycles[31:24];
            rbuf[6] <= chk;
            rlen <= 4'd7; cnt <= 4'd0; state <= S_TX;
        end
        S_TX: if (!tx_busy && !tx_send && !tx_wait) begin
            if (cnt == rlen) state <= S_CMD;
            else begin
                tx_data <= rbuf[cnt[2:0]]; tx_send <= 1'b1; tx_wait <= 1'b1;
                cnt <= cnt + 4'd1;
            end
        end
        default: state <= S_CMD;
        endcase
    end

    // ------------------------------------------------------------ LEDs
    reg [24:0] hb = 25'd0;
    always @(posedge clk) hb <= hb + 1'b1;
    wire busy = (state == S_RUN) || (state == S_WAIT);
    assign led_n   = ~{cfg_led, rx_led, hb[24], marker, busy, tok_led};
    assign trig_out = marker;
endmodule
