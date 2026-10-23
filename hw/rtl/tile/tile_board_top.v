// tile_board_top.v -- one L tile (behavioural block RAM, AW words of 16 bit) on the Sipeed Tang Nano 20K, driven over UART.
// Same ports as lookup_board_top, so ../../board/tangnano20k.cst works unchanged. 27 MHz clock, 8N1, 115200 baud.
// Protocol (host -> board), flits are 72 bit = 9 bytes, most significant byte first:
//   54 'T' f0..f8   inject one flit at the client port of the tile. Lookup (type 0): reply 9 bytes of the response flit.
//                   Update (type 2, posted add): reply 4B 'K' once accepted.
//   45 'E'          ping. Reply 5A.
// LEDs (active low): led[0] toggles per injected flit, led[1] tile busy (request waiting), led[3] heartbeat.
// PROTOTYPE: single tile, no neighbours (dst must be tile 0,0); the hashed table is therefore one tile's bank (AW=12 -> 8 KB; AW=15 -> 64 KB).
module tile_board_top #(parameter CLK_HZ = 27_000_000, parameter BAUD = 115200, parameter POR_BITS = 16, parameter AW = 12) (
    input clk, input btn_s1, input btn_s2, input uart_rx, output uart_tx, output [5:0] led_n, output trig_out);
    localparam FW = 72;
    reg [POR_BITS:0] por = 0; always @(posedge clk) if (!por[POR_BITS]) por <= por + 1'b1;
    reg btn_m = 0, btn_s = 0; always @(posedge clk) begin btn_m <= btn_s1; btn_s <= btn_m; end
    reg rst = 1; always @(posedge clk) rst <= ~por[POR_BITS] | btn_s;
    wire [7:0] rx_data; wire rx_valid; reg [7:0] tx_data = 0; reg tx_send = 0; wire tx_busy;
    uart_rx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) u_rx (.clk(clk), .rst(rst), .rx(uart_rx), .data(rx_data), .valid(rx_valid));
    uart_tx #(.CLK_HZ(CLK_HZ), .BAUD(BAUD)) u_tx (.clk(clk), .rst(rst), .send(tx_send), .data(tx_data), .tx(uart_tx), .busy(tx_busy));
    reg cv = 0; reg [FW-1:0] cf = 0; wire cr; wire rv; wire [FW-1:0] rf; reg rr = 0;
    wire [4*FW-1:0] z1, z2; wire [3:0] v1, v2;
    l_tile #(0, 0, AW, FW) tile (.clk(clk), .rst(rst), .cl_req_valid(cv), .cl_req_flit(cf), .cl_req_ready(cr), .cl_rsp_valid(rv), .cl_rsp_flit(rf), .cl_rsp_ready(rr),
        .rq_in_flit({4*FW{1'b0}}), .rq_in_valid(4'b0), .rq_in_ready(), .rq_out_flit(z1), .rq_out_valid(v1), .rq_out_ready(4'hF),
        .rp_in_flit({4*FW{1'b0}}), .rp_in_valid(4'b0), .rp_in_ready(), .rp_out_flit(z2), .rp_out_valid(v2), .rp_out_ready(4'hF));
    localparam S_IDLE = 0, S_RX = 1, S_INJ = 2, S_WAIT = 3, S_TX = 4, S_ACK = 5;
    reg [2:0] st = S_IDLE; reg [3:0] n = 0; reg [FW-1:0] sh = 0; reg [7:0] tog = 0; reg [24:0] hb = 0;
    always @(posedge clk) begin
        tx_send <= 0; rr <= 0; hb <= hb + 1'b1;
        if (rst) begin st <= S_IDLE; cv <= 0; n <= 0; end
        else case (st)
            S_IDLE: if (rx_valid) begin
                if (rx_data == 8'h54) begin st <= S_RX; n <= 0; end
                else if (rx_data == 8'h45) begin tx_data <= 8'h5A; tx_send <= 1; end end
            S_RX: if (rx_valid) begin sh <= {sh[FW-9:0], rx_data}; n <= n + 1'b1; if (n == 4'd8) st <= S_INJ; end
            S_INJ: begin cf <= sh; cv <= 1; if (cv && cr) begin cv <= 0; tog[0] <= ~tog[0]; st <= (sh[FW-1:FW-2] == 2'd0) ? S_WAIT : S_ACK; n <= 0; end end
            S_WAIT: if (rv) begin sh <= rf; rr <= 1; st <= S_TX; n <= 0; end
            S_TX: if (!tx_busy && !tx_send) begin
                    tx_data <= sh[FW-1:FW-8]; tx_send <= 1; sh <= {sh[FW-9:0], 8'h00}; n <= n + 1'b1; if (n == 4'd8) st <= S_IDLE; end
            S_ACK: if (!tx_busy && !tx_send) begin tx_data <= 8'h4B; tx_send <= 1; st <= S_IDLE; end
        endcase
    end
    assign led_n = ~{2'b00, 1'b0, hb[24], (st != S_IDLE), tog[0]};
    assign trig_out = (st == S_WAIT);
endmodule
