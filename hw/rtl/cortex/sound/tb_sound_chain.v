// Testbench: replays sound_cmds.hex on cortex_sound_top. Per command: op, arg, clip (0xffff = none). LEARN (1) and
// PREDICT (4) first stream clip `clip` into the chip sample by sample (raw samples from clips.hex), then run with
// lb_len = code length.
// Output lines as tb_cortex_core.v (U / D / P, then N per class and W / C per code bit) in sound_out.txt.
`timescale 1ns/1ps
module tb_sound_chain;
    parameter NCLIP = 2, NW = 100, NB = 23040, CB = 10;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg smp_valid = 0; reg [15:0] smp_data = 0; wire smp_ready;
    reg tm_we = 0; reg [9:0] tm_addr = 0; reg [24:0] tm_data = 0;
    reg lane_we = 0; reg [4:0] lane_waddr = 0; reg [31:0] lane_wdata = 0;
    reg hear = 0, cmd_valid = 0; reg [2:0] cmd_op = 0; reg [3:0] cmd_arg = 0; reg [15:0] lb_len = 0; reg [14:0] mem_addr = 0;
    wire hear_done, busy, updated; wire [15:0] hear_count, llen_out; wire [3:0] pred; wire [49:0] rd_w; wire [99:0] rd_c, rd_n;
    cortex_sound_top dut(.clk(clk), .rst(rst), .smp_valid(smp_valid), .smp_data(smp_data), .smp_ready(smp_ready),
        .tm_we(tm_we), .tm_addr(tm_addr), .tm_data(tm_data), .lane_we(lane_we), .lane_waddr(lane_waddr), .lane_wdata(lane_wdata),
        .hear(hear), .hear_done(hear_done), .hear_count(hear_count), .cmd_valid(cmd_valid), .cmd_op(cmd_op), .cmd_arg(cmd_arg),
        .lb_len(lb_len), .mem_addr(mem_addr), .busy(busy), .pred(pred), .updated(updated), .llen_out(llen_out),
        .rd_w(rd_w), .rd_c(rd_c), .rd_n(rd_n));
    reg [15:0] clips [0:NCLIP*16000-1]; reg [24:0] tmpl [0:639]; reg [31:0] seeds [0:31]; reg [31:0] cmds [0:NW-1];
    integer f, p, q, op, clip, b, c, ncmd;
    task run(input [2:0] o, input [3:0] a); begin
        @(negedge clk); cmd_op = o; cmd_arg = a; cmd_valid = 1; @(negedge clk); cmd_valid = 0;
        while (busy) @(negedge clk);
    end endtask
    initial begin
        $readmemh("clips.hex", clips); $readmemh("tmpl.hex", tmpl); $readmemh("lanes.hex", seeds); $readmemh("sound_cmds.hex", cmds);
        f = $fopen("sound_out.txt", "w");
        repeat (3) @(negedge clk); rst = 0;
        for (q = 0; q < 640; q = q + 1) begin @(negedge clk); tm_we = 1; tm_addr = q; tm_data = tmpl[q]; end
        @(negedge clk); tm_we = 0;
        for (q = 0; q < 32; q = q + 1) begin @(negedge clk); lane_we = 1; lane_waddr = q; lane_wdata = seeds[q]; end
        @(negedge clk); lane_we = 0;
        run(3'd6, 4'd0);                                          // CLEAR
        p = 0; ncmd = 0;
        while (p < NW && cmds[p] !== 32'hxxxxxxxx && cmds[p] != 32'hffffffff) begin
            op = cmds[p]; cmd_arg = cmds[p + 1]; clip = cmds[p + 2]; p = p + 3;
            if (op == 1 || op == 4) begin
                @(negedge clk); hear = 1; @(negedge clk); hear = 0; q = 0;
                while (!hear_done) begin                      // stream the clip, one sample whenever the cochlea is ready
                    if (smp_ready && q < 16000) begin smp_valid = 1; smp_data = clips[clip * 16000 + q]; q = q + 1; end
                    else smp_valid = 0;
                    @(negedge clk);
                end
                smp_valid = 0;
                @(negedge clk); lb_len = hear_count;
            end
            @(negedge clk); cmd_op = op; cmd_valid = 1; @(negedge clk); cmd_valid = 0;
            while (busy) @(negedge clk);
            if (op == 4) $fdisplay(f, "P %0d", pred);
            else if (op == 1) $fdisplay(f, "U %0d", updated);
            else if (op == 3) $fdisplay(f, "D %0d %0d", llen_out, updated);
            ncmd = ncmd + 1;
        end
        for (c = 0; c < 10; c = c + 1) $fdisplay(f, "N %0d", rd_n[c*CB +: CB]);
        for (b = 0; b < NB; b = b + 1) begin mem_addr = b; run(3'd7, 4'd0); $fdisplay(f, "W %h C %h", rd_w, rd_c); end
        $fclose(f); $display("commands %0d, cycles %0t", ncmd, $time / 10); $finish;
    end
endmodule
