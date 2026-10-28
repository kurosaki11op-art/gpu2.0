// L board top (28 Oct 2026, SIMULATED with a UART model; not run on a board): a UART front end for l_chip_top so a PC can drive the layers.
// Protocol (8N1): the host sends 0xA5, then an op byte.
//   op 0x01 RECOGNISE: 772 bytes follow (the 6,176 input bits, bit i in byte i/8 at position i%8). Reply, 7 bytes: 0x5A, routed, pred, cycles (4 bytes, little endian).
//   op 0x02 MATMUL: runs the Forge tile on its resident matrices. Reply: 0x5B, cycles (4 bytes), then 256 outputs of 5 bytes (macc as 3 bytes sign-extended, eacc as 2 bytes sign-extended).
module l_board_top #(parameter CLK_HZ = 27_000_000, parameter BAUD = 115200) (
    input clk, input rst, input rx, output tx, output led_deep, output led_forge);
    wire [7:0] rxd; wire rxv; reg [7:0] tx_d = 0; reg tx_s = 0; wire tx_busy;
    uart_rx #(CLK_HZ, BAUD) u_rx (.clk(clk), .rst(rst), .rx(rx), .data(rxd), .valid(rxv));
    uart_tx #(CLK_HZ, BAUD) u_tx (.clk(clk), .rst(rst), .send(tx_s), .data(tx_d), .tx(tx), .busy(tx_busy));
    reg op = 0, start = 0, wr_en = 0; reg [12:0] wr_addr = 0; reg wr_bit = 0; reg [7:0] c_raddr = 0;
    wire busy, done, routed; wire [3:0] pred; wire [199:0] sc; wire ca, da, fa; wire signed [16:0] cm; wire signed [11:0] ce; wire [31:0] cyc;
    l_chip_top core (.clk(clk), .rst(rst), .op(op), .start(start), .wr_en(wr_en), .wr_addr(wr_addr), .wr_bit(wr_bit), .busy(busy), .done(done), .routed(routed), .pred(pred), .scores_flat(sc),
                     .cortex_active(ca), .deep_active(da), .forge_active(fa), .c_raddr(c_raddr), .c_macc(cm), .c_eacc(ce), .cycles(cyc));
    assign led_deep = da; assign led_forge = fa;
    // byte sender: the main FSM raises sb_go with sb_data; a byte is taken when the transmitter is idle
    reg sb_go = 0; reg [7:0] sb_data = 0; reg sb_busy = 0, seen = 0; wire taken = sb_go && !sb_busy && !tx_busy;
    always @(posedge clk) begin
        tx_s <= 0;
        if (rst) begin sb_busy <= 0; seen <= 0; end
        else if (!sb_busy) begin if (taken) begin tx_d <= sb_data; tx_s <= 1; sb_busy <= 1; seen <= 0; end end
        else begin if (tx_busy) seen <= 1; else if (seen) sb_busy <= 0; end
    end
    localparam S_IDLE = 0, S_OP = 1, S_LOAD = 2, S_BITS = 3, S_RUN = 4, S_HDR = 5, S_EWAIT = 6, S_ESEND = 7;
    reg [3:0] st = S_IDLE; reg [9:0] nbytes = 0; reg [3:0] bitn = 0; reg [7:0] cur = 0; reg mm_mode = 0; reg [3:0] hi = 0; reg [8:0] el = 0; reg [2:0] lane = 0; reg [1:0] ew = 0; reg [31:0] cyc_l = 0; reg r_routed = 0; reg [3:0] r_pred = 0;
    wire [3:0] hdr_len = mm_mode ? 5 : 7;
    always @(posedge clk) begin
        start <= 0; wr_en <= 0;
        if (rst) st <= S_IDLE;
        else case (st)
            S_IDLE: if (rxv && rxd == 8'hA5) st <= S_OP;
            S_OP: if (rxv) begin
                if (rxd == 8'h01) begin op <= 0; mm_mode <= 0; nbytes <= 0; wr_addr <= 0; st <= S_LOAD; end
                else if (rxd == 8'h02) begin op <= 1; mm_mode <= 1; start <= 1; st <= S_RUN; end
                else st <= S_IDLE; end
            S_LOAD: if (rxv) begin cur <= rxd; bitn <= 0; st <= S_BITS; end
            S_BITS: if (bitn == 8) begin nbytes <= nbytes + 1; wr_addr <= wr_addr + 1; if (nbytes == 771) begin start <= 1; st <= S_RUN; end else st <= S_LOAD; end
                    else begin wr_en <= 1; wr_bit <= cur[bitn[2:0]]; if (bitn != 0) wr_addr <= wr_addr + 1; bitn <= bitn + 1; end
            S_RUN: if (done) begin cyc_l <= cyc; r_routed <= routed; r_pred <= pred; hi <= 0; sb_go <= 1; sb_data <= (mm_mode ? 8'h5B : 8'h5A); st <= S_HDR; end
            S_HDR: if (taken) begin
                       if (hi + 1 == hdr_len) begin sb_go <= 0; if (mm_mode) begin el <= 0; c_raddr <= 0; ew <= 0; st <= S_EWAIT; end else st <= S_IDLE; end
                       else begin hi <= hi + 1; sb_data <= (mm_mode) ? ((hi + 1 == 1) ? cyc_l[7:0] : (hi + 1 == 2) ? cyc_l[15:8] : (hi + 1 == 3) ? cyc_l[23:16] : cyc_l[31:24])
                                                                   : ((hi + 1 == 1) ? {7'b0, r_routed} : (hi + 1 == 2) ? {4'b0, r_pred} : (hi + 1 == 3) ? cyc_l[7:0] : (hi + 1 == 4) ? cyc_l[15:8] : (hi + 1 == 5) ? cyc_l[23:16] : cyc_l[31:24]); end
                   end
            S_EWAIT: begin ew <= ew + 1; if (ew == 2) begin lane <= 0; sb_go <= 1; sb_data <= cm[7:0]; st <= S_ESEND; end end
            S_ESEND: if (taken) begin
                         if (lane == 4) begin sb_go <= 0; if (el == 255) st <= S_IDLE; else begin el <= el + 1; c_raddr <= el + 1; ew <= 0; st <= S_EWAIT; end end
                         else begin lane <= lane + 1; sb_data <= (lane + 1 == 1) ? cm[15:8] : (lane + 1 == 2) ? {8{cm[16]}} : (lane + 1 == 3) ? ce[7:0] : {{4{ce[11]}}, ce[11:8]}; end
                     end
            default: st <= S_IDLE;
        endcase
    end
endmodule
