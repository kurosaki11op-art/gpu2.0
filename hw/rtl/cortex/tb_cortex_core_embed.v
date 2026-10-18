// Testbench for the CORTEX_EMBED build: as tb_cortex_core.v, plus op 13 = ENROLL, op 14 = WINNER, op 15 = MATCH (MEM args 8-10; the word after the op is the mem_addr value); prints 'V slot' / 'M slot label dist';
// at the end every prototype element (MEM arg 11) and slot meta (arg 12) is written as 'E <int>' / 'T <hex>'. Writes out_cortex.txt.
`timescale 1ns/1ps
module tb_cortex_core_embed;
    parameter NB = 4608, AW = 13, CB = 10, NW = 1000, NPS = 48, SW = 20;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg cmd_valid = 0; reg [2:0] cmd_op = 0; reg [3:0] cmd_arg = 0;
    reg lb_we = 0; reg [AW-1:0] lb_waddr = 0, lb_wdata = 0; reg [AW:0] lb_len = 0;
    reg lane_we = 0; reg [4:0] lane_waddr = 0; reg [31:0] lane_wdata = 0;
    wire [5:0] emb_slot; wire [3:0] emb_lab; wire [23:0] emb_dist; wire signed [SW-1:0] rd_e; wire busy, updated; wire [3:0] pred; wire [AW:0] llen_out;
    reg [AW-1:0] mem_addr = 0; wire [49:0] rd_w; wire [10*CB-1:0] rd_c, rd_n; wire [9:0] rd_known;
    cortex_core #(.NB(NB), .AW(AW), .CB(CB)) dut(.clk(clk), .rst(rst), .cmd_valid(cmd_valid), .cmd_op(cmd_op),
        .cmd_arg(cmd_arg), .lb_we(lb_we), .lb_waddr(lb_waddr), .lb_wdata(lb_wdata), .lb_len(lb_len),
        .lane_we(lane_we), .lane_waddr(lane_waddr), .lane_wdata(lane_wdata),
        .mem_addr(mem_addr), .wr_w(50'd0), .wr_c({(10*CB){1'b0}}),
        .busy(busy), .pred(pred), .updated(updated), .llen_out(llen_out), .emb_slot(emb_slot), .emb_lab(emb_lab), .emb_dist(emb_dist), .rd_e(rd_e), .rd_w(rd_w), .rd_c(rd_c), .rd_n(rd_n), .rd_known(rd_known));
    task run(input [2:0] o, input [3:0] a); begin
        @(negedge clk); cmd_op = o; cmd_arg = a; cmd_valid = 1; @(negedge clk); cmd_valid = 0;
        while (busy) @(negedge clk);
    end endtask
    reg [31:0] cmds [0:NW-1]; reg [31:0] seeds [0:31];
    integer p, q, f, len, op, ncmd; integer b, c; reg [31:0] argw;
    initial begin
        $readmemh("cmds.hex", cmds); $readmemh("lanes.hex", seeds);
        f = $fopen("out_cortex.txt", "w");
        repeat (3) @(negedge clk); rst = 0;
        for (q = 0; q < 32; q = q + 1) begin
            @(negedge clk); lane_we = 1; lane_waddr = q; lane_wdata = seeds[q];
        end
        @(negedge clk); lane_we = 0;
        run(3'd6, 4'd0);                                       // CLEAR: memories start at zero, as in the model
        p = 0; ncmd = 0;
        while (p < NW && cmds[p] !== 32'hxxxxxxxx && cmds[p] != 32'hffffffff) begin
            op = cmds[p]; argw = cmds[p + 1]; cmd_arg = cmds[p + 1]; len = cmds[p + 2]; p = p + 3;
            for (q = 0; q < len; q = q + 1) begin
                @(negedge clk); lb_we = 1; lb_waddr = q; lb_wdata = cmds[p + q];
            end
            p = p + len;
            @(negedge clk); lb_we = 0; lb_len = len; cmd_valid = 1;
            cmd_op = (op >= 13) ? 3'd7 : op; if (op == 13) begin mem_addr = argw[AW-1:0]; cmd_arg = 4'd8; end if (op == 14) begin mem_addr = argw[AW-1:0]; cmd_arg = 4'd9; end if (op == 15) begin mem_addr = argw[AW-1:0]; cmd_arg = 4'd10; end
            @(negedge clk); cmd_valid = 0;
            while (busy) @(negedge clk);
            if (op == 4) $fdisplay(f, "P %0d", pred);
            else if (op == 14) $fdisplay(f, "V %0d", emb_slot);
            else if (op == 15) $fdisplay(f, "M %0d %0d %0d", emb_slot, emb_lab, emb_dist);
            else if (op == 1 || op == 2) $fdisplay(f, "U %0d", updated);
            else if (op == 3) $fdisplay(f, "D %0d %0d", llen_out, updated);
            ncmd = ncmd + 1;
        end
        for (c = 0; c < 10; c = c + 1) $fdisplay(f, "N %0d", rd_n[c*CB +: CB]);
        for (b = 0; b < NB; b = b + 1) begin mem_addr = b; run(3'd7, 4'd0); $fdisplay(f, "W %h C %h", rd_w, rd_c); end
        for (b = 0; b < NPS * 16; b = b + 1) begin mem_addr = b; run(3'd7, 4'd11); $fdisplay(f, "E %0d", rd_e); end
        for (b = 0; b < NPS; b = b + 1) begin mem_addr = b; run(3'd7, 4'd12); $fdisplay(f, "T %h", rd_e & 20'h1fff); end
        $fclose(f); $display("commands %0d, cycles %0t", ncmd, $time / 10); $finish;
    end
endmodule
