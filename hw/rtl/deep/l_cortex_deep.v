// L Cortex + L Deep on one interface (28 Oct 2026, SIMULATED/verified): the EXISTING Cortex blocks do stage 1 -- cortex_encoder (ENC_S1, finer grid) turns the image into the active code
// bits, cortex_core (CORTEX_SLOW, CORTEX_HOOKS) scores them with its slow table (loaded by SLOAD, MEM arg 13) and reports the margin -- and the dispatcher wakes L Deep stage 2
// (l_system with S1 = 0) when the margin is <= ROUTE_T. Deep's bit memory holds the code bits (cleared, then set from the encoder's list) and the two raw-pixel threshold planes.
// Host: load detectors (tm_*), the stage-1 table (tbl_we, one 80-bit word per code bit), pixels (pix_we), then start; wait for done. busy is high while a table word is being written.
`timescale 1ns/1ps
module l_cortex_deep #(parameter ROUTE_T = 2299, NCL = 2000, NLITS = 13497) (
    input clk, input rst,
    input tm_we, input [1:0] tm_ch, input [4:0] tm_f, input [24:0] tm_data,
    input tbl_we, input [12:0] tbl_addr, input [79:0] tbl_data,
    input pix_we, input [9:0] pix_addr, input [7:0] pix_data,
    input start,
    output reg busy, output reg done, output reg routed, output reg [3:0] pred, output reg [199:0] scores_flat,
    output reg [31:0] cycles, output reg [31:0] cyc_enc, cyc_core, cyc_deep, output reg err_overlap);
    reg [7:0] pimg [0:783];
    always @(posedge clk) if (pix_we) pimg[pix_addr] <= pix_data;
    // ---- encoder
    reg e_start; wire e_busy, e_done, e_we; wire [13:0] e_count; wire [12:0] e_addr, e_data;
    cortex_encoder #(.AW(13)) u_enc (.clk(clk), .rst(rst), .pix_we(pix_we), .pix_addr(pix_addr), .pix_data(pix_data), .tm_we(tm_we), .tm_ch(tm_ch), .tm_f(tm_f), .tm_data(tm_data),
        .start(e_start), .busy(e_busy), .done(e_done), .count(e_count), .out_we(e_we), .out_addr(e_addr), .out_data(e_data));
    // ---- core
    reg c_valid; reg [2:0] c_op; reg [3:0] c_arg; reg [12:0] c_maddr; reg [99:0] c_wc; reg [13:0] c_len;
    wire c_busy; wire [3:0] c_pred; wire c_upd; wire [13:0] c_llen; wire signed [19:0] c_margin; wire [31:0] c_wrc; wire [199:0] c_sc; wire [79:0] c_rds; wire [49:0] c_rdw; wire [99:0] c_rdc, c_rdn; wire [9:0] c_known;
    cortex_core #(.NB(4608), .AW(13)) u_core (.clk(clk), .rst(rst), .cmd_valid(c_valid), .cmd_op(c_op), .cmd_arg(c_arg), .lb_we(e_we), .lb_waddr(e_addr), .lb_wdata(e_data), .lb_len(c_len),
        .lane_we(1'b0), .lane_waddr(5'd0), .lane_wdata(32'd0), .mem_addr(c_maddr), .wr_w(50'd0), .wr_c(c_wc), .busy(c_busy), .pred(c_pred), .updated(c_upd), .llen_out(c_llen),
        .top_margin(c_margin), .wr_count(c_wrc), .rd_scores(c_sc), .rd_s(c_rds), .rd_w(c_rdw), .rd_c(c_rdc), .rd_n(c_rdn), .rd_known(c_known));
    // ---- Deep stage 2
    reg d_wr; reg [12:0] d_addr; reg d_bit; reg d_start; wire d_busy, d_done, d_routed; wire [3:0] d_pred; wire [199:0] d_sc; wire [31:0] d_cyc; wire d_act;
    l_system #(.ROUTE_T(ROUTE_T), .NCL(NCL), .NLITS(NLITS), .S1(0)) u_deep (.clk(clk), .rst(rst), .wr_en(d_wr), .wr_addr(d_addr), .wr_bit(d_bit), .start(d_start),
        .busy(d_busy), .done(d_done), .routed(d_routed), .pred(d_pred), .scores_flat(d_sc), .cycles(d_cyc), .s2_active());
    // ---- control
    localparam T_IDLE = 0, T_TBL = 1, T_TBLW = 2, T_KN = 3, T_KNW = 4, T_RUN = 5, T_PRED = 6, T_PREDW = 7, T_PREDW2 = 8, T_D = 9, T_DW = 10;
    reg [3:0] st; reg [3:0] kn; reg [13:0] sw; reg sweep_done; reg [2:0] sph; reg [9:0] spx; reg sph_b; reg have_enc; reg [13:0] cnt_l;
    reg init_done;
    wire signed [19:0] m = c_margin;
    always @(posedge clk) begin
        if (rst) begin st <= T_IDLE; busy <= 0; done <= 0; c_valid <= 0; e_start <= 0; d_start <= 0; d_wr <= 0; init_done <= 0; kn <= 0; err_overlap <= 0; cycles <= 0; sweep_done <= 1; routed <= 0; pred <= 0; end
        else begin
            done <= 0; c_valid <= 0; e_start <= 0; d_start <= 0; d_wr <= 0;
            if (st != T_IDLE && st != T_TBL && st != T_TBLW) cycles <= cycles + 1;
            // the bit memory of Deep: sweep (zeros over the code bits, then the pixel planes), then the encoder's list sets ones
            if (!sweep_done) begin
                d_wr <= 1;
                if (sph == 0) begin d_addr <= sw; d_bit <= 0; if (sw == 4607) begin sph <= 1; spx <= 0; sph_b <= 0; end else sw <= sw + 1; end
                else begin
                    d_addr <= 4608 + (sph_b ? 784 : 0) + spx; d_bit <= sph_b ? (pimg[spx] > 8'd170) : (pimg[spx] > 8'd85);
                    if (!sph_b) sph_b <= 1; else begin sph_b <= 0; if (spx == 783) begin sweep_done <= 1; end else spx <= spx + 1; end
                end
            end else if (e_we) begin d_wr <= 1; d_addr <= e_data; d_bit <= 1; end
            if (e_we && !sweep_done) err_overlap <= 1;
            case (st)
                T_IDLE: begin
                    if (!init_done) begin st <= T_KN; busy <= 1; kn <= 0; end
                    else if (tbl_we) begin c_valid <= 1; c_op <= 3'd7; c_arg <= 4'd13; c_maddr <= tbl_addr; c_wc <= {20'd0, tbl_data}; busy <= 1; st <= T_TBLW; end
                    else if (start) begin e_start <= 1; sweep_done <= 0; sw <= 0; sph <= 0; busy <= 1; cycles <= 0; cyc_enc <= 0; cyc_core <= 0; cyc_deep <= 0; routed <= 0; st <= T_RUN; end
                end
                T_TBLW: if (!c_valid && !c_busy) begin busy <= 0; st <= T_IDLE; end
                T_KN: begin c_valid <= 1; c_op <= 3'd5; c_arg <= kn; st <= T_KNW; end
                T_KNW: if (!c_valid && !c_busy) begin if (kn == 9) begin init_done <= 1; busy <= 0; st <= T_IDLE; end else begin kn <= kn + 1; st <= T_KN; end end
                T_RUN: begin cyc_enc <= cyc_enc + 1; if (e_done) begin c_len <= e_count; st <= T_PRED; end end
                T_PRED: begin c_valid <= 1; c_op <= 3'd4; c_arg <= 4'd0; st <= T_PREDW; end
                T_PREDW: begin cyc_core <= cyc_core + 1; if (!c_valid && !c_busy) st <= T_PREDW2; end
                T_PREDW2: begin
                    scores_flat <= c_sc; pred <= c_pred; routed <= 0;
                    if (m <= ROUTE_T) begin routed <= 1; d_start <= 1; st <= T_DW; end else begin done <= 1; busy <= 0; st <= T_IDLE; end
                end
                T_DW: begin cyc_deep <= cyc_deep + 1; if (d_done) begin scores_flat <= d_sc; pred <= d_pred; done <= 1; busy <= 0; st <= T_IDLE; end end
                default: st <= T_IDLE;
            endcase
        end
    end
endmodule
