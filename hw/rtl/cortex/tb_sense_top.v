// Testbench: replays sense_cmds.hex on cortex_sense_top. Per command 4 words: op, arg, picture index, clip index (0xffff = none). LEARN (1) and PREDICT (4) first show the picture (pix_we, then see) and / or play the clip (hear, then the samples
// whenever smp_ready), then run with lb_len = code_len. Output lines in sense_out.txt: U / P as tb_sound_chain, then N per class and W / C per code bit.
`timescale 1ns/1ps
module tb_sense_top;
    parameter NPIC = 4, NCLIP = 2, NW = 400, NB = 9216, CB = 10;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg pix_we = 0; reg [9:0] pix_addr = 0; reg [7:0] pix_data = 0; reg tmv_we = 0, tma_we = 0; reg [8:0] tmv_addr = 0, tma_addr = 0; reg [24:0] tmv_data = 0, tma_data = 0;
    reg see = 0, hear = 0; wire see_done, hear_done; wire [14:0] see_count, hear_count, code_len, llen_out;
    reg smp_valid = 0; reg [15:0] smp_data = 0; wire smp_ready;
    reg lane_we = 0; reg [4:0] lane_waddr = 0; reg [31:0] lane_wdata = 0;
    reg cmd_valid = 0; reg [2:0] cmd_op = 0; reg [3:0] cmd_arg = 0; reg [14:0] lb_len = 0; reg [13:0] mem_addr = 0;
    wire busy, updated; wire [3:0] pred; wire [49:0] rd_w; wire [99:0] rd_c, rd_n;
    cortex_sense_top dut(.clk(clk), .rst(rst), .pix_we(pix_we), .pix_addr(pix_addr), .pix_data(pix_data), .tmv_we(tmv_we), .tmv_addr(tmv_addr), .tmv_data(tmv_data),
        .see(see), .see_done(see_done), .see_count(see_count), .smp_valid(smp_valid), .smp_data(smp_data), .smp_ready(smp_ready), .tma_we(tma_we), .tma_addr(tma_addr), .tma_data(tma_data),
        .hear(hear), .hear_done(hear_done), .hear_count(hear_count), .lane_we(lane_we), .lane_waddr(lane_waddr), .lane_wdata(lane_wdata),
        .cmd_valid(cmd_valid), .cmd_op(cmd_op), .cmd_arg(cmd_arg), .lb_len(lb_len), .code_len(code_len), .mem_addr(mem_addr),
        .busy(busy), .pred(pred), .updated(updated), .llen_out(llen_out), .rd_w(rd_w), .rd_c(rd_c), .rd_n(rd_n), .rd_known());
    reg [7:0] pics [0:NPIC*784-1]; reg [15:0] clips [0:NCLIP*16000-1]; reg [24:0] tv [0:127]; reg [24:0] ta [0:127]; reg [31:0] seeds [0:31]; reg [31:0] cmds [0:NW-1];
    integer f, p, q, op, pi, ci, b, c, ncmd;
    task run(input [2:0] o, input [3:0] a); begin
        @(negedge clk); cmd_op = o; cmd_arg = a; cmd_valid = 1; @(negedge clk); cmd_valid = 0;
        while (busy) @(negedge clk);
    end endtask
    initial begin
        $readmemh("pics.hex", pics); $readmemh("clips.hex", clips); $readmemh("tmpl_v.hex", tv); $readmemh("tmpl_a.hex", ta); $readmemh("lanes.hex", seeds); $readmemh("sense_cmds.hex", cmds);
        f = $fopen("sense_out.txt", "w");
        repeat (3) @(negedge clk); rst = 0;
        for (q = 0; q < 128; q = q + 1) begin @(negedge clk); tmv_we = 1; tmv_addr = q; tmv_data = tv[q]; tma_we = 1; tma_addr = q; tma_data = ta[q]; end
        @(negedge clk); tmv_we = 0; tma_we = 0;
        for (q = 0; q < 32; q = q + 1) begin @(negedge clk); lane_we = 1; lane_waddr = q; lane_wdata = seeds[q]; end
        @(negedge clk); lane_we = 0;
        run(3'd6, 4'd0);                                          // CLEAR
        p = 0; ncmd = 0;
        while (p < NW && cmds[p] !== 32'hxxxxxxxx && cmds[p] != 32'hffffffff) begin
            op = cmds[p]; cmd_arg = cmds[p + 1]; pi = cmds[p + 2]; ci = cmds[p + 3]; p = p + 4;
            if (op == 1 || op == 4) begin
                if (pi != 32'hffff) begin
                    for (q = 0; q < 784; q = q + 1) begin @(negedge clk); pix_we = 1; pix_addr = q; pix_data = pics[pi * 784 + q]; end
                    @(negedge clk); pix_we = 0; see = 1; @(negedge clk); see = 0;
                    while (!see_done) @(negedge clk);
                end
                if (ci != 32'hffff) begin
                    @(negedge clk); hear = 1; @(negedge clk); hear = 0; q = 0;
                    while (!hear_done) begin
                        if (smp_ready && q < 16000) begin smp_valid = 1; smp_data = clips[ci * 16000 + q]; q = q + 1; end
                        else smp_valid = 0;
                        @(negedge clk);
                    end
                    smp_valid = 0;
                end
                @(negedge clk); lb_len = code_len;
            end
            @(negedge clk); cmd_op = op; cmd_valid = 1; @(negedge clk); cmd_valid = 0;
            while (busy) @(negedge clk);
            if (op == 4) $fdisplay(f, "P %0d", pred);
            else if (op == 1) $fdisplay(f, "U %0d", updated);
            ncmd = ncmd + 1;
        end
        for (c = 0; c < 10; c = c + 1) $fdisplay(f, "N %0d", rd_n[c*CB +: CB]);
        for (b = 0; b < NB; b = b + 1) begin mem_addr = b; run(3'd7, 4'd0); $fdisplay(f, "W %h C %h", rd_w, rd_c); end
        $fclose(f); $display("commands %0d, cycles %0t", ncmd, $time / 10); $finish;
    end
endmodule
