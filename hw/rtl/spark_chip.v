// spark_chip.v -- SPARK chip top: spark_core + UART host interface, 8 signal pins.
// ASIC-ready: external active-low reset (synchronised), every register reset explicitly, weights written
// into the on-chip SRAMs over UART (silicon has no preloaded memories).
//
// Pins: clk, rst_n, uart_rx, uart_tx, ready (memory clear done), busy (token running),
//       tok (toggles per token), trig_out (benchmark marker for the power logger).
//
// UART 8N1. Host -> chip commands (the chip answers each before the next is sent):
//   0xC0 c0..c7            config (same encoding as hw/board/spark_board_top.v)    reply 0xC1
//   0xB0 sel aL aH d0..d3  write one 32-bit weight word: memory sel (0 emb, 1..4 w0..w3, 5 emb1, 6 emb2),
//                          12-bit word address, data little-endian                  reply 0xB1
//   0xD0 b                 run one token; reply pred, path, cyc[31:0] LE, xor-checksum (7 bytes)
//   0xE0                   ping, reply 0x5A
//   0xA0 / 0xA1            marker pin low / high, reply echo
module spark_chip #(
    parameter CLK_HZ = 27_000_000,
    parameter BAUD   = 115200
) (
    input  clk,
    input  rst_n,
    input  uart_rx,
    output uart_tx,
    output ready,
    output busy,
    output tok,
    output trig_out
);
    // ------------------------------------------------------------ reset synchroniser
    reg [1:0] rs;
    always @(posedge clk or negedge rst_n) if (!rst_n) rs <= 2'b11; else rs <= {rs[0], 1'b0};
    wire rst = rs[1];

    // ------------------------------------------------------------ UART
    wire [7:0] rx_data; wire rx_valid;
    reg  [7:0] tx_data; reg tx_send; wire tx_busy;
    uart_rx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) u_rx (.clk(clk), .rst(rst), .rx(uart_rx), .data(rx_data), .valid(rx_valid));
    uart_tx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) u_tx (.clk(clk), .rst(rst), .send(tx_send), .data(tx_data), .tx(uart_tx), .busy(tx_busy));

    // ------------------------------------------------------------ configuration
    reg        sparse_en, delta_en, exit_en, recall_en, adapt_en, thr_en;
    reg [15:0] cap; reg [31:0] exit_th; reg [1:0] conf_th, recall_mode; reg [15:0] arb_th;

    // ------------------------------------------------------------ core
    reg        start; reg [7:0] in_byte;
    reg        ld_we; reg [2:0] ld_sel; reg [11:0] ld_addr; reg [31:0] ld_data;
    wire       done, core_ready; wire [7:0] pred; wire [1:0] path; wire [31:0] tok_cycles;
    wire [31:0] wreads, ce, cs, cp, cr; wire [15:0] a0, a1, a2, a3, b0, b1, b2, b3;
    spark_core u_core (
        .clk(clk), .rst(rst), .start(start), .in_byte(in_byte),
        .sparse_en(sparse_en), .delta_en(delta_en), .exit_en(exit_en), .recall_en(recall_en),
        .cap(cap), .recall_mode(recall_mode), .arb_th(arb_th), .exit_th(exit_th), .conf_th(conf_th),
        .cfg_a(9'd230), .acc_sh(4'd2), .s_sh(4'd4), .adapt_en(adapt_en), .thr_en(thr_en),
        .ld_we(ld_we), .ld_sel(ld_sel), .ld_addr(ld_addr), .ld_data({32'd0, ld_data}),
        .done(done), .ready(core_ready), .pred(pred), .path(path), .tok_cycles(tok_cycles), .wreads(wreads),
        .cyc_engine(ce), .cyc_scan(cs), .cyc_post(cp), .cyc_recall(cr),
        .nz0(a0), .nz1(a1), .nz2(a2), .nz3(a3), .pr0(b0), .pr1(b1), .pr2(b2), .pr3(b3));

    // ------------------------------------------------------------ command FSM
    localparam S_CMD = 3'd0, S_CFG = 3'd1, S_DATA = 3'd2, S_RUN = 3'd3, S_WAIT = 3'd4, S_TX = 3'd5, S_LD = 3'd6;
    reg [2:0] state; reg [3:0] cnt, rlen; reg [7:0] cfgb [0:7]; reg [7:0] rbuf [0:6];
    reg marker, tok_t, tx_wait;
    wire [7:0] chk = pred ^ {6'd0, path} ^ tok_cycles[7:0] ^ tok_cycles[15:8] ^ tok_cycles[23:16] ^ tok_cycles[31:24];

    always @(posedge clk) begin
        start <= 1'b0; tx_send <= 1'b0; tx_wait <= 1'b0; ld_we <= 1'b0;
        if (rst) begin
            state <= S_CMD; cnt <= 4'd0; rlen <= 4'd0; marker <= 1'b0; tok_t <= 1'b0; tx_data <= 8'd0;
            in_byte <= 8'd0; ld_sel <= 3'd0; ld_addr <= 12'd0; ld_data <= 32'd0;
            sparse_en <= 1'b1; delta_en <= 1'b0; exit_en <= 1'b0; recall_en <= 1'b0; adapt_en <= 1'b0; thr_en <= 1'b1;
            cap <= 16'd0; exit_th <= 32'd64; conf_th <= 2'd1; recall_mode <= 2'd0; arb_th <= 16'd64;
        end else case (state)
        S_CMD: if (rx_valid) begin
            cnt <= 4'd0;
            case (rx_data)
            8'hC0, 8'hB0: state <= (rx_data == 8'hC0) ? S_CFG : S_LD;
            8'hD0: state <= S_DATA;
            8'hE0: begin rbuf[0] <= 8'h5A; rlen <= 4'd1; state <= S_TX; end
            8'hA0, 8'hA1: begin marker <= rx_data[0]; rbuf[0] <= rx_data; rlen <= 4'd1; state <= S_TX; end
            default: ;
            endcase
        end
        S_CFG: if (rx_valid) begin
            cfgb[cnt[2:0]] <= rx_data; cnt <= cnt + 4'd1;
            if (cnt == 4'd7) begin
                sparse_en <= cfgb[0][0]; delta_en <= cfgb[0][1]; exit_en <= cfgb[0][2];
                recall_en <= cfgb[0][3]; adapt_en <= cfgb[0][4]; thr_en <= cfgb[0][5];
                cap <= {cfgb[2], cfgb[1]}; exit_th <= {cfgb[6], cfgb[5], cfgb[4], cfgb[3]};
                conf_th <= rx_data[1:0]; recall_mode <= rx_data[3:2]; arb_th <= {8'd0, rx_data[7:4], 4'd0};
                rbuf[0] <= 8'hC1; rlen <= 4'd1; cnt <= 4'd0; state <= S_TX;
            end
        end
        S_LD: if (rx_valid) begin                       // sel, aL, aH, d0, d1, d2, d3
            cfgb[cnt[2:0]] <= rx_data; cnt <= cnt + 4'd1;
            if (cnt == 4'd6) begin
                ld_sel <= cfgb[0][2:0]; ld_addr <= {cfgb[2][3:0], cfgb[1]};
                ld_data <= {rx_data, cfgb[5], cfgb[4], cfgb[3]}; ld_we <= 1'b1;
                rbuf[0] <= 8'hB1; rlen <= 4'd1; cnt <= 4'd0; state <= S_TX;
            end
        end
        S_DATA: if (rx_valid) begin in_byte <= rx_data; state <= S_RUN; end
        S_RUN:  begin start <= 1'b1; state <= S_WAIT; end
        S_WAIT: if (done) begin
            tok_t <= ~tok_t;
            rbuf[0] <= pred; rbuf[1] <= {6'd0, path};
            rbuf[2] <= tok_cycles[7:0]; rbuf[3] <= tok_cycles[15:8]; rbuf[4] <= tok_cycles[23:16]; rbuf[5] <= tok_cycles[31:24];
            rbuf[6] <= chk; rlen <= 4'd7; cnt <= 4'd0; state <= S_TX;
        end
        S_TX: if (!tx_busy && !tx_send && !tx_wait) begin
            if (cnt == rlen) state <= S_CMD;
            else begin tx_data <= rbuf[cnt[2:0]]; tx_send <= 1'b1; tx_wait <= 1'b1; cnt <= cnt + 4'd1; end
        end
        default: state <= S_CMD;
        endcase
    end

    assign ready = core_ready;
    assign busy = (state == S_RUN) || (state == S_WAIT);
    assign tok = tok_t;
    assign trig_out = marker;
endmodule
