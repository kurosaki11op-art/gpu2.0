// SPARK Cortex for sound (simulation / ASIC top, no UART): live 16 kHz samples -> streaming cochlea
// (cortex_cochlea_stream.v, with its noise floor and, ALIGN = 1, word alignment to frame LEAD) -> 28x28 sound picture
// -> sensory encoder (cortex_encoder_gen.v, 10 channels x 64 detectors) -> 23,040-bit code written into the learning
// core's list (cortex_core.v, NB = 23,040).
// Pulse hear, then stream the clip's samples (smp_valid / smp_ready); hear_done pulses with the code length in
// hear_count; then give the core its command (LEARN c / PREDICT / DREAM ...) with lb_len = hear_count. Detectors
// (tm_*) and random lanes (lane_*) are loaded once.
`timescale 1ns/1ps
module cortex_sound_top #(parameter ALIGN = 1, parameter LEAD = 6) (
    input  wire        clk, rst,
    input  wire        smp_valid, input wire [15:0] smp_data, output wire smp_ready,
    input  wire        tm_we, input wire [9:0] tm_addr, input wire [24:0] tm_data,
    input  wire        lane_we, input wire [4:0] lane_waddr, input wire [31:0] lane_wdata,
    input  wire        hear, output reg hear_done, output reg [15:0] hear_count,
    input  wire        cmd_valid, input wire [2:0] cmd_op, input wire [3:0] cmd_arg, input wire [15:0] lb_len,
    input  wire [14:0] mem_addr,
    output wire        busy, output wire [3:0] pred, output wire updated, output wire [15:0] llen_out,
    output wire [49:0] rd_w, output wire [99:0] rd_c, output wire [99:0] rd_n
);
    wire c_busy, c_done, px_we; wire [9:0] px_addr; wire [7:0] px_data;
    wire e_busy, e_done, e_we; wire [15:0] e_count; wire [14:0] e_addr, e_data;
    reg  e_start;
    cortex_cochlea_stream #(.ALIGN(ALIGN), .LEAD(LEAD)) u_coch (.clk(clk), .rst(rst), .start(hear), .smp_valid(smp_valid), .smp_data(smp_data),
        .smp_ready(smp_ready), .busy(c_busy), .done(c_done), .px_we(px_we), .px_addr(px_addr), .px_data(px_data));
    cortex_encoder_gen #(.NCH(10), .F(64), .LF(6),
        .THR({8'd8, 8'd8, 8'd230, 8'd200, 8'd170, 8'd140, 8'd110, 8'd80, 8'd50, 8'd20}),
        .KIND({2'd2, 2'd1, 16'd0}), .AW(15)) u_enc (.clk(clk), .rst(rst),
        .pix_we(px_we), .pix_addr(px_addr), .pix_data(px_data), .tm_we(tm_we), .tm_addr(tm_addr), .tm_data(tm_data),
        .start(e_start), .busy(e_busy), .done(e_done), .count(e_count), .out_we(e_we), .out_addr(e_addr), .out_data(e_data));
    wire [9:0] rd_known;
    cortex_core #(.NB(23040), .AW(15)) u_core (.clk(clk), .rst(rst), .cmd_valid(cmd_valid), .cmd_op(cmd_op), .cmd_arg(cmd_arg),
        .lb_we(e_we), .lb_waddr(e_addr), .lb_wdata(e_data), .lb_len(lb_len),
        .lane_we(lane_we), .lane_waddr(lane_waddr), .lane_wdata(lane_wdata),
        .mem_addr(mem_addr), .wr_w(50'd0), .wr_c(100'd0),
        .busy(busy), .pred(pred), .updated(updated), .llen_out(llen_out), .rd_w(rd_w), .rd_c(rd_c), .rd_n(rd_n), .rd_known(rd_known));
    always @(posedge clk) begin
        e_start <= c_done; hear_done <= e_done;               // cochlea done -> encoder starts; encoder done -> heard
        if (e_done) hear_count <= e_count;
    end
endmodule
