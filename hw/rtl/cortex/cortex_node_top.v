// SPARK Cortex node (22 Oct 2026): raw senses to a whole learning stage on one chip. cortex_sense_top (retina + cochlea encoders and the core) driven by cortex_seq (the stage and night sequencer).
// The host only shows each example to the senses (picture: pix_we then see; sound: hear then the samples) and pulses ex_valid with the label when the senses are done; ex_ready says the sequencer can take the next example.
// Everything else (KNOWN, LEARN with lb_len = code_len, daydreams, interleaved dreams, FOLLOW every CH ticks, the night with its early stop, SCOPY) is issued by the sequencer. h_cmd_* lets the host read the memories (MEM command) when no stage runs.
`timescale 1ns/1ps
module cortex_node_top #(parameter ALIGN = 1, parameter LEAD = 6, parameter NBS = 4608, parameter CHMIN = 100, parameter CHSH = 5) (
    input  wire        clk, rst,
    input  wire        pix_we, input wire [9:0] pix_addr, input wire [7:0] pix_data,
    input  wire        tmv_we, input wire [8:0] tmv_addr, input wire [24:0] tmv_data,
    input  wire        see, output wire see_done, output wire [14:0] see_count,
    input  wire        smp_valid, input wire [15:0] smp_data, output wire smp_ready,
    input  wire        tma_we, input wire [8:0] tma_addr, input wire [24:0] tma_data,
    input  wire        hear, output wire hear_done, output wire [14:0] hear_count,
    input  wire        lane_we, input wire [4:0] lane_waddr, input wire [31:0] lane_wdata,
    input  wire        cfg_we, input wire [2:0] cfg_addr, input wire [31:0] cfg_val, input wire start, input wire ex_valid, input wire [3:0] ex_label, output wire ex_ready, output wire done,
    input  wire        h_cmd_valid, input wire [2:0] h_cmd_op, input wire [3:0] h_cmd_arg,
    input  wire [13:0] mem_addr,
    output wire        busy, output wire updated, output wire [14:0] llen_out, output wire [3:0] pred,
    output wire [49:0] rd_w, output wire [99:0] rd_c, output wire [99:0] rd_n, output wire [9:0] rd_known
);
    wire sq_valid; wire [2:0] sq_op; wire [3:0] sq_arg; wire [14:0] code_len;
    wire cv = h_cmd_valid | sq_valid; wire [2:0] co = h_cmd_valid ? h_cmd_op : sq_op; wire [3:0] ca = h_cmd_valid ? h_cmd_arg : sq_arg;
    cortex_sense_top #(.ALIGN(ALIGN), .LEAD(LEAD), .NBS(NBS)) u_sense (.clk(clk), .rst(rst), .pix_we(pix_we), .pix_addr(pix_addr), .pix_data(pix_data), .tmv_we(tmv_we), .tmv_addr(tmv_addr), .tmv_data(tmv_data),
        .see(see), .see_done(see_done), .see_count(see_count), .smp_valid(smp_valid), .smp_data(smp_data), .smp_ready(smp_ready), .tma_we(tma_we), .tma_addr(tma_addr), .tma_data(tma_data),
        .hear(hear), .hear_done(hear_done), .hear_count(hear_count), .lane_we(lane_we), .lane_waddr(lane_waddr), .lane_wdata(lane_wdata),
        .cmd_valid(cv), .cmd_op(co), .cmd_arg(ca), .lb_len(code_len), .code_len(code_len), .mem_addr(mem_addr),
        .busy(busy), .pred(pred), .updated(updated), .llen_out(llen_out), .rd_w(rd_w), .rd_c(rd_c), .rd_n(rd_n), .rd_known(rd_known));
    cortex_seq #(.C(10), .CHMIN(CHMIN), .CHSH(CHSH)) u_seq (.clk(clk), .rst(rst), .cfg_we(cfg_we), .cfg_addr(cfg_addr), .cfg_val(cfg_val), .start(start), .ex_valid(ex_valid), .ex_label(ex_label), .ex_ready(ex_ready), .done(done),
        .cmd_valid(sq_valid), .cmd_op(sq_op), .cmd_arg(sq_arg), .busy(busy), .updated(updated), .known(rd_known));
endmodule
