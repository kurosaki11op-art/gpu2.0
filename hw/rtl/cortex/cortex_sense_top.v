// SPARK Cortex with two senses (20 Oct 2026): a retina (28x28 picture -> cortex_encoder_gen, 4 channels x 32 detectors, 4,608-bit code) and a cochlea
// (live 16 kHz samples -> cortex_cochlea_stream with noise floor and word alignment -> 28x28 sound picture -> cortex_encoder_gen, 4 channels x 32 detectors,
// 4,608-bit code) write into ONE list of the learning core (cortex_core.v, NB = 9,216): picture bits first (index 0..4607), sound bits after them (index 4608..9215).
// Use: pulse see (the picture was loaded with pix_we) and / or pulse hear then stream the clip (smp_valid / smp_ready); when see_done / hear_done have pulsed,
// give the core its command (LEARN c / PREDICT / DREAM ...) with lb_len = code_len; the senses are forgotten when the command is issued (one sense only is fine:
// a picture alone, or a sound alone, fills the list the same way, the sound bits keep their 4608 offset). See before hear when both are used.
// Detectors: tmv_* (picture encoder) and tma_* (sound encoder), tm_addr = channel * 32 + detector, 25 bits; random lanes lane_*, loaded once.
`timescale 1ns/1ps
module cortex_sense_top #(parameter ALIGN = 1, parameter LEAD = 6, parameter NBS = 4608) (
    input  wire        clk, rst,
    input  wire        pix_we, input wire [9:0] pix_addr, input wire [7:0] pix_data,
    input  wire        tmv_we, input wire [8:0] tmv_addr, input wire [24:0] tmv_data,
    input  wire        see, output reg see_done, output reg [14:0] see_count,
    input  wire        smp_valid, input wire [15:0] smp_data, output wire smp_ready,
    input  wire        tma_we, input wire [8:0] tma_addr, input wire [24:0] tma_data,
    input  wire        hear, output reg hear_done, output reg [14:0] hear_count,
    input  wire        lane_we, input wire [4:0] lane_waddr, input wire [31:0] lane_wdata,
    input  wire        cmd_valid, input wire [2:0] cmd_op, input wire [3:0] cmd_arg, input wire [14:0] lb_len,
    output wire [14:0] code_len,
    input  wire [13:0] mem_addr,
    output wire        busy, output wire [3:0] pred, output wire updated, output wire [14:0] llen_out,
    output wire [49:0] rd_w, output wire [99:0] rd_c, output wire [99:0] rd_n, output wire [9:0] rd_known
);
    // retina
    wire v_busy, v_done, v_we; wire [14:0] v_count; wire [13:0] v_addr, v_data;
    cortex_encoder_gen #(.NCH(4), .F(32), .LF(5), .THR({8'd8, 8'd8, 8'd150, 8'd50}), .KIND({2'd2, 2'd1, 2'd0, 2'd0}), .AW(14)) u_eye (.clk(clk), .rst(rst),
        .pix_we(pix_we), .pix_addr(pix_addr), .pix_data(pix_data), .tm_we(tmv_we), .tm_addr(tmv_addr), .tm_data(tmv_data),
        .start(see), .busy(v_busy), .done(v_done), .count(v_count), .out_we(v_we), .out_addr(v_addr), .out_data(v_data));
    // cochlea + sound encoder (3x3 windows at stride 1, 4x4 pooling: WH = WW = 3, LS = 0, NS = 26, LP = 2, NC = 6, MINON = 1; channels 50, 110, 170 and the on-cells)
    wire c_busy, c_done, px_we; wire [9:0] px_addr; wire [7:0] px_data; wire a_busy, a_done, a_we; wire [14:0] a_count; wire [13:0] a_addr, a_data; reg a_start;
    cortex_cochlea_stream #(.ALIGN(ALIGN), .LEAD(LEAD)) u_coch (.clk(clk), .rst(rst), .start(hear), .smp_valid(smp_valid), .smp_data(smp_data),
        .smp_ready(smp_ready), .busy(c_busy), .done(c_done), .px_we(px_we), .px_addr(px_addr), .px_data(px_data));
    cortex_encoder_gen #(.NCH(4), .F(32), .LF(5), .THR({8'd8, 8'd170, 8'd110, 8'd50}), .KIND({2'd1, 6'd0}), .AW(14),
                         .WH(3), .WW(3), .LS(0), .NS(26), .LP(2), .NC(6), .MINON(1)) u_ear (.clk(clk), .rst(rst),
        .pix_we(px_we), .pix_addr(px_addr), .pix_data(px_data), .tm_we(tma_we), .tm_addr(tma_addr), .tm_data(tma_data),
        .start(a_start), .busy(a_busy), .done(a_done), .count(a_count), .out_we(a_we), .out_addr(a_addr), .out_data(a_data));
    // which senses are in the list for the next command
    reg seen, heard; reg [14:0] s_cnt, h_cnt;
    assign code_len = (seen ? s_cnt : 15'd0) + (heard ? h_cnt : 15'd0);
    wire [14:0] a_base = seen ? s_cnt : 15'd0;
    wire        l_we   = v_we | a_we;
    wire [13:0] l_addr = v_we ? v_addr : (a_addr + a_base[13:0]);
    wire [13:0] l_data = v_we ? v_data : (a_data + NBS[13:0]);
    cortex_core #(.NB(2 * NBS), .AW(14)) u_core (.clk(clk), .rst(rst), .cmd_valid(cmd_valid), .cmd_op(cmd_op), .cmd_arg(cmd_arg),
        .lb_we(l_we), .lb_waddr(l_addr), .lb_wdata(l_data), .lb_len(lb_len),
        .lane_we(lane_we), .lane_waddr(lane_waddr), .lane_wdata(lane_wdata),
        .mem_addr(mem_addr), .wr_w(50'd0), .wr_c(100'd0),
        .busy(busy), .pred(pred), .updated(updated), .llen_out(llen_out), .rd_w(rd_w), .rd_c(rd_c), .rd_n(rd_n), .rd_known(rd_known));
    always @(posedge clk) begin
        a_start <= c_done; see_done <= v_done; hear_done <= a_done;
        if (v_done) begin see_count <= v_count; s_cnt <= v_count; seen <= 1'b1; end
        if (a_done) begin hear_count <= a_count; h_cnt <= a_count; heard <= 1'b1; end
        if (cmd_valid) begin seen <= 1'b0; heard <= 1'b0; end
        if (rst) begin seen <= 1'b0; heard <= 1'b0; end
    end
endmodule
