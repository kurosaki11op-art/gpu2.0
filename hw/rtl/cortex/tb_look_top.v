// Two cores (coarse table A and fine table B, different code widths) + the second-look unit: tables are imported over the MEM interface, then every case loads the two code lists, runs PREDICT on both
// cores and reads the decision of cortex_look. look_top_in.hex (64-bit words): [0] threshold, [1] known mask, [2] number of cases, [3..] table A words, table B words, then per case: lenA, listA, lenB, listB.
// Writes "pred look scoreA0 scoreB0" per case to look_top_out.txt.
`timescale 1ns/1ps
module tb_look_top;
    parameter NA = 640, AWA = 10, NBW = 1024, AWB = 10, C = 10, WB = 5, CB = 10, SW = 20, NMAX = 20000;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg va = 0, vb = 0; reg [2:0] opa = 0, opb = 0; reg [3:0] arga = 0, argb = 0;
    reg lba = 0, lbb = 0; reg [AWA-1:0] lbaa = 0, lbad = 0; reg [AWB-1:0] lbba = 0, lbbd = 0; reg [AWA:0] lena = 0; reg [AWB:0] lenb = 0;
    reg [AWA-1:0] ma = 0; reg [AWB-1:0] mb = 0; reg [C*WB-1:0] wra = 0, wrb = 0;
    wire busya, busyb, upda, updb; wire [3:0] preda, predb; wire [AWA:0] lla; wire [AWB:0] llb; wire [C*WB-1:0] rdwa, rdwb; wire [C*CB-1:0] rdca, rdcb, rdna, rdnb; wire [C-1:0] kna, knb;
    wire signed [SW-1:0] tma, tmb; wire [31:0] wca, wcb; wire [C*SW-1:0] sca, scb;
    cortex_core #(.NB(NA), .AW(AWA)) A(.clk(clk), .rst(rst), .cmd_valid(va), .cmd_op(opa), .cmd_arg(arga), .lb_we(lba), .lb_waddr(lbaa), .lb_wdata(lbad), .lb_len(lena), .lane_we(1'b0), .lane_waddr(5'd0), .lane_wdata(32'd0),
        .mem_addr(ma), .wr_w(wra), .wr_c({(C*CB){1'b0}}), .busy(busya), .pred(preda), .updated(upda), .llen_out(lla), .top_margin(tma), .wr_count(wca), .rd_scores(sca), .rd_w(rdwa), .rd_c(rdca), .rd_n(rdna), .rd_known(kna));
    cortex_core #(.NB(NBW), .AW(AWB)) B(.clk(clk), .rst(rst), .cmd_valid(vb), .cmd_op(opb), .cmd_arg(argb), .lb_we(lbb), .lb_waddr(lbba), .lb_wdata(lbbd), .lb_len(lenb), .lane_we(1'b0), .lane_waddr(5'd0), .lane_wdata(32'd0),
        .mem_addr(mb), .wr_w(wrb), .wr_c({(C*CB){1'b0}}), .busy(busyb), .pred(predb), .updated(updb), .llen_out(llb), .top_margin(tmb), .wr_count(wcb), .rd_scores(scb), .rd_w(rdwb), .rd_c(rdcb), .rd_n(rdnb), .rd_known(knb));
    reg [C-1:0] known; reg [SW:0] th; wire [3:0] pred; wire look;
    cortex_look #(.C(C), .SW(SW)) U(.sa(sca), .sb(scb), .known(known), .th(th), .pred(pred), .look(look));
    reg [63:0] mem [0:NMAX]; integer f, p, n, ncase, q, len;
    initial begin
        $readmemh("look_top_in.hex", mem); f = $fopen("look_top_out.txt", "w"); th = mem[0]; known = mem[1]; ncase = mem[2]; p = 3;
        repeat (3) @(negedge clk); rst = 0; @(negedge clk);
        for (q = 0; q < NA; q = q + 1) begin ma = q; wra = mem[p]; p = p + 1; @(negedge clk); opa = 3'd7; arga = 4'd1; va = 1; @(negedge clk); va = 0; while (busya) @(negedge clk); end
        for (q = 0; q < NBW; q = q + 1) begin mb = q; wrb = mem[p]; p = p + 1; @(negedge clk); opb = 3'd7; argb = 4'd1; vb = 1; @(negedge clk); vb = 0; while (busyb) @(negedge clk); end
        for (n = 0; n < ncase; n = n + 1) begin
            len = mem[p]; p = p + 1; for (q = 0; q < len; q = q + 1) begin @(negedge clk); lba = 1; lbaa = q; lbad = mem[p + q]; end p = p + len; @(negedge clk); lba = 0; lena = len;
            len = mem[p]; p = p + 1; for (q = 0; q < len; q = q + 1) begin @(negedge clk); lbb = 1; lbba = q; lbbd = mem[p + q]; end p = p + len; @(negedge clk); lbb = 0; lenb = len;
            @(negedge clk); opa = 3'd4; arga = 0; va = 1; opb = 3'd4; argb = 0; vb = 1; @(negedge clk); va = 0; vb = 0; while (busya || busyb) @(negedge clk);
            #1; $fdisplay(f, "%0d %0d %0d %0d", pred, look, $signed(sca[SW-1:0]), $signed(scb[SW-1:0]));
        end
        $fclose(f); $display("cases %0d", ncase); $finish;
    end
endmodule
