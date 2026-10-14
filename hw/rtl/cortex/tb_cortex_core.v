// Testbench: replays a command stream (cmds.hex) on cortex_core and dumps results (out_cortex.txt) and final memories.
// cmds.hex: 32-bit words, per command: op, arg, len, then len code-bit indices. lanes.hex: 32 lane seeds.
`timescale 1ns/1ps
module tb_cortex_core;
    parameter NB = 4608, AW = 13, CB = 10, NW = 1000;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg cmd_valid = 0; reg [2:0] cmd_op = 0; reg [3:0] cmd_arg = 0;
    reg lb_we = 0; reg [AW-1:0] lb_waddr = 0, lb_wdata = 0; reg [AW:0] lb_len = 0;
    reg lane_we = 0; reg [4:0] lane_waddr = 0; reg [31:0] lane_wdata = 0;
    wire busy, updated; wire [3:0] pred; wire [AW:0] llen_out;
    cortex_core #(.NB(NB), .AW(AW), .CB(CB)) dut(.clk(clk), .rst(rst), .cmd_valid(cmd_valid), .cmd_op(cmd_op),
        .cmd_arg(cmd_arg), .lb_we(lb_we), .lb_waddr(lb_waddr), .lb_wdata(lb_wdata), .lb_len(lb_len),
        .lane_we(lane_we), .lane_waddr(lane_waddr), .lane_wdata(lane_wdata),
        .busy(busy), .pred(pred), .updated(updated), .llen_out(llen_out));
    reg [31:0] cmds [0:NW-1]; reg [31:0] seeds [0:31];
    integer p, q, f, len, op, ncmd; integer b, c;
    initial begin
        $readmemh("cmds.hex", cmds); $readmemh("lanes.hex", seeds);
        for (b = 0; b < NB; b = b + 1) begin dut.wmem[b] = 0; dut.cmem[b] = 0; end
        f = $fopen("out_cortex.txt", "w");
        repeat (3) @(negedge clk); rst = 0;
        for (q = 0; q < 32; q = q + 1) begin
            @(negedge clk); lane_we = 1; lane_waddr = q; lane_wdata = seeds[q];
        end
        @(negedge clk); lane_we = 0;
        p = 0; ncmd = 0;
        while (p < NW && cmds[p] !== 32'hxxxxxxxx && cmds[p] != 32'hffffffff) begin
            op = cmds[p]; cmd_arg = cmds[p + 1]; len = cmds[p + 2]; p = p + 3;
            for (q = 0; q < len; q = q + 1) begin
                @(negedge clk); lb_we = 1; lb_waddr = q; lb_wdata = cmds[p + q];
            end
            p = p + len;
            @(negedge clk); lb_we = 0; lb_len = len; cmd_op = op; cmd_valid = 1;
            @(negedge clk); cmd_valid = 0;
            while (busy) @(negedge clk);
            if (op == 4) $fdisplay(f, "P %0d", pred);
            else if (op == 1 || op == 2) $fdisplay(f, "U %0d", updated);
            else if (op == 3) $fdisplay(f, "D %0d %0d", llen_out, updated);
            ncmd = ncmd + 1;
        end
        for (c = 0; c < 10; c = c + 1) $fdisplay(f, "N %0d", dut.n[c]);
        for (b = 0; b < NB; b = b + 1) $fdisplay(f, "W %h C %h", dut.wmem[b], dut.cmem[b]);
        $fclose(f); $display("commands %0d, cycles %0t", ncmd, $time / 10); $finish;
    end
endmodule
