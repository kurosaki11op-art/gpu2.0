// Testbench: cortex_core (CORTEX_SLOW) driven by cortex_seq. seq_in.hex: [0] number of stages; per stage: ndream, night, daydream, ch, nstop, N, newmask, then N x (label, length, list). The testbench only loads each example's list into the core and pulses ex_valid;
// everything else (KNOWN, LEARN, DREAM, FOLLOW, SCOPY, the night and its early stop) is issued by the sequencer. At the end it dumps N, every fast word and every slow word like tb_cortex_core_slow.v (out_cortex.txt).
`timescale 1ns/1ps
module tb_seq_pred;
    parameter NB = 256, AW = 8, CB = 10, MARGIN = 32, NW = 40000, SB = 8, CHMIN = 100, CHSH = 5;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    wire cmd_valid; wire [2:0] cmd_op; wire [3:0] cmd_arg;
    reg lb_we = 0; reg [AW-1:0] lb_waddr = 0, lb_wdata = 0; reg [AW:0] lb_len = 0;
    reg lane_we = 0; reg [4:0] lane_waddr = 0; reg [31:0] lane_wdata = 0; reg [AW-1:0] mem_addr = 0;
    wire [10*SB-1:0] rd_s; wire busy, updated; wire [3:0] pred; wire [AW:0] llen_out; wire [49:0] rd_w; wire [10*CB-1:0] rd_c, rd_n; wire [9:0] rd_known;
    reg cmd_valid_h = 0; reg [2:0] cmd_op_h = 0; reg [3:0] cmd_arg_h = 0; reg use_h = 0;
    wire cv = use_h ? cmd_valid_h : cmd_valid; wire [2:0] co = use_h ? cmd_op_h : cmd_op; wire [3:0] ca = use_h ? cmd_arg_h : cmd_arg;
    cortex_core #(.NB(NB), .AW(AW), .CB(CB), .MARGIN(MARGIN)) dut(.clk(clk), .rst(rst), .cmd_valid(cv), .cmd_op(co), .cmd_arg(ca), .lb_we(lb_we), .lb_waddr(lb_waddr), .lb_wdata(lb_wdata), .lb_len(lb_len),
        .lane_we(lane_we), .lane_waddr(lane_waddr), .lane_wdata(lane_wdata), .mem_addr(mem_addr), .wr_w(50'd0), .wr_c({(10*CB){1'b0}}),
        .busy(busy), .pred(pred), .updated(updated), .llen_out(llen_out), .rd_s(rd_s), .rd_w(rd_w), .rd_c(rd_c), .rd_n(rd_n), .rd_known(rd_known));
    reg cfg_we = 0; reg [2:0] cfg_addr = 0; reg [31:0] cfg_val = 0; reg start = 0, ex_valid = 0; reg [3:0] ex_label = 0; wire ex_ready, done;
    cortex_seq #(.C(10), .CHMIN(CHMIN), .CHSH(CHSH)) seq(.clk(clk), .rst(rst), .cfg_we(cfg_we), .cfg_addr(cfg_addr), .cfg_val(cfg_val), .start(start), .ex_valid(ex_valid), .ex_label(ex_label), .ex_ready(ex_ready), .done(done),
        .cmd_valid(cmd_valid), .cmd_op(cmd_op), .cmd_arg(cmd_arg), .busy(busy), .updated(updated), .known(rd_known));
    task cfg(input [2:0] a, input [31:0] v); begin @(negedge clk); cfg_we = 1; cfg_addr = a; cfg_val = v; @(negedge clk); cfg_we = 0; end endtask
    task hrun(input [2:0] o, input [3:0] a); begin
        @(negedge clk); use_h = 1; cmd_op_h = o; cmd_arg_h = a; cmd_valid_h = 1; @(negedge clk); cmd_valid_h = 0; while (busy) @(negedge clk); use_h = 0;
    end endtask
    reg [31:0] mem [0:NW-1]; reg [31:0] seeds [0:31]; integer p, q, f, ns, s, n, e, len, nex, b, c, ncyc, ntest, tt;
    initial begin
        $readmemh("seq_in.hex", mem); $readmemh("lanes.hex", seeds); f = $fopen("out_cortex.txt", "w");
        repeat (3) @(negedge clk); rst = 0;
        for (q = 0; q < 32; q = q + 1) begin @(negedge clk); lane_we = 1; lane_waddr = q; lane_wdata = seeds[q]; end
        @(negedge clk); lane_we = 0; hrun(3'd6, 4'd0);                     // CLEAR
        ns = mem[0]; p = 1;
        for (s = 0; s < ns; s = s + 1) begin
            cfg(3'd0, mem[p]); cfg(3'd1, mem[p+1]); cfg(3'd2, mem[p+2]); cfg(3'd3, mem[p+3]); cfg(3'd4, mem[p+4]); cfg(3'd5, mem[p+5]); cfg(3'd6, mem[p+6]); nex = mem[p+5]; p = p + 7;
            @(negedge clk); start = 1; @(negedge clk); start = 0;
            for (e = 0; e < nex; e = e + 1) begin
                while (!ex_ready) @(negedge clk);
                len = mem[p+1];
                for (q = 0; q < len; q = q + 1) begin @(negedge clk); lb_we = 1; lb_waddr = q; lb_wdata = mem[p + 2 + q]; end
                @(negedge clk); lb_we = 0; lb_len = len; ex_label = mem[p]; ex_valid = 1; @(negedge clk); ex_valid = 0; p = p + 2 + len;
            end
            ncyc = 0; while (!done) begin @(negedge clk); ncyc = ncyc + 1; end
        end
        ntest = mem[p]; p = p + 1;
        for (tt = 0; tt < ntest; tt = tt + 1) begin
            len = mem[p]; p = p + 1;
            for (q = 0; q < len; q = q + 1) begin @(negedge clk); lb_we = 1; lb_waddr = q; lb_wdata = mem[p + q]; end
            p = p + len; @(negedge clk); lb_we = 0; lb_len = len; hrun(3'd4, 4'd0); $fdisplay(f, "P %0d", pred);
        end
        for (c = 0; c < 10; c = c + 1) $fdisplay(f, "N %0d", rd_n[c*CB +: CB]);
        $fclose(f); $display("stages %0d", ns); $finish;
    end
endmodule
