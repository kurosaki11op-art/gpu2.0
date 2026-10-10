`timescale 1ns/1ps
// Feeds stim.hex bytes through spark_core one token at a time and writes
// one result line per token to rtl_out.txt:
//   pred path nz0 nz1 nz2 nz3 pr0 pr1 pr2 pr3 tok_cycles wreads engine scan post recall
// Config via plusargs: +sparse= +delta= +exit= +exit_th= +recall= +conf_th= +rmode= +arb_th= +cap= +n= +dump_from= +dump_n=
module tb_asic_dbg;  // tb_spark_core + weight loading through the ld_* port (SRAMs have no power-on contents)
    reg clk = 0, rst = 1, start = 0;
    reg [7:0] in_byte = 0;
    integer sparse_en = 1, delta_en = 0, exit_en = 0, exit_th = 64, recall_en = 0,
            conf_th = 1, rmode = 0, arb_th = 64, cap = 0, dump_from = -1, dump_n = 20, adapt = 0, thr = 0, n = 0, a = 230, acc_sh = 2, s_sh = 4;
    reg [7:0] stim [0:65535];
    reg ld_we = 0; reg [2:0] ld_sel = 0; reg [11:0] ld_addr = 0; reg [31:0] ld_data = 0;
    reg [31:0] wbuf [0:4095];
    task load(input [2:0] sel, input integer depth);
        integer i;
        begin
            for (i = 0; i < depth; i = i + 1) begin
                @(negedge clk); ld_we = 1; ld_sel = sel; ld_addr = i; ld_data = wbuf[i];
            end
            @(negedge clk); ld_we = 0;
        end
    endtask
    integer t, f;
    wire done; wire [7:0] pred; wire [1:0] path;
    wire [31:0] tok_cycles, wreads, cyc_engine, cyc_scan, cyc_post, cyc_recall;
    wire [15:0] nz0, nz1, nz2, nz3, pr0, pr1, pr2, pr3;

    spark_core dut (
        .clk(clk), .rst(rst), .start(start), .in_byte(in_byte),
        .sparse_en(sparse_en[0]), .delta_en(delta_en[0]), .exit_en(exit_en[0]),
        .recall_en(recall_en[0]), .cap(cap[15:0]), .recall_mode(rmode[1:0]), .arb_th(arb_th[15:0]), .exit_th(exit_th),
        .conf_th(conf_th[1:0]), .cfg_a(a[8:0]), .acc_sh(acc_sh[3:0]), .s_sh(s_sh[3:0]), .adapt_en(adapt[0]), .thr_en(thr[0]),
        .ld_we(ld_we), .ld_sel(ld_sel), .ld_addr(ld_addr), .ld_data({32'd0, ld_data}),
        .done(done), .pred(pred), .path(path), .tok_cycles(tok_cycles), .wreads(wreads),
        .cyc_engine(cyc_engine), .cyc_scan(cyc_scan), .cyc_post(cyc_post),
        .cyc_recall(cyc_recall),
        .nz0(nz0), .nz1(nz1), .nz2(nz2), .nz3(nz3), .pr0(pr0), .pr1(pr1), .pr2(pr2), .pr3(pr3)
    );

    always #5 clk = ~clk;
    integer dbg_n = 0;
    always @(posedge clk) if ($test$plusargs("trace") && start === 1'b0 && dbg_n < 400 && dut.state != 0) begin
        dbg_n = dbg_n + 1;
        $display("t=%0t state=%0d stg=%0d c=%0d m=%0d mask=%b emb_rd=%h w0_rd=%h", $time, dut.state, dut.stg, dut.c, dut.m, dut.mask, dut.emb_rd, dut.w0_rd);
    end   // 100 MHz simulation clock (timing is not modelled)

    initial begin
        void'($value$plusargs("sparse=%d", sparse_en));
        void'($value$plusargs("delta=%d", delta_en));
        void'($value$plusargs("exit=%d", exit_en));
        void'($value$plusargs("exit_th=%d", exit_th));
        void'($value$plusargs("recall=%d", recall_en));
        void'($value$plusargs("conf_th=%d", conf_th));
        void'($value$plusargs("cap=%d", cap));
        void'($value$plusargs("rmode=%d", rmode));
        void'($value$plusargs("arb_th=%d", arb_th));
        void'($value$plusargs("n=%d", n));
        void'($value$plusargs("adapt=%d", adapt));
        void'($value$plusargs("thr=%d", thr));
        void'($value$plusargs("a=%d", a));
        void'($value$plusargs("acc_sh=%d", acc_sh));
        void'($value$plusargs("s_sh=%d", s_sh));
        void'($value$plusargs("dump_from=%d", dump_from));
        void'($value$plusargs("dump_n=%d", dump_n));
        if (dump_from >= 0) begin           // switching-activity window for power simulation
            $dumpfile("act.vcd"); $dumpvars(0, dut); $dumpoff;
        end
        $readmemh("stim.hex", stim);
        f = $fopen("rtl_out.txt", "w");
        repeat (3) @(posedge clk);
        rst = 0;
        @(posedge clk);
        $readmemh("emb.hex", wbuf);  load(3'd0, 2048);
        $readmemh("emb1.hex", wbuf); load(3'd5, 2048);
        $readmemh("emb2.hex", wbuf); load(3'd6, 2048);
        $readmemh("w0.hex", wbuf);   load(3'd1, 3072);
        $readmemh("w1.hex", wbuf);   load(3'd2, 2048);
        $readmemh("w2.hex", wbuf);   load(3'd3, 4096);
        $readmemh("w3.hex", wbuf);   load(3'd4, 4096);
        $display("weights loaded through ld_* port");
        for (t = 0; t < n; t = t + 1) begin
            @(negedge clk);
            if (dump_from >= 0 && t == dump_from) $dumpon;
            if (dump_from >= 0 && t == dump_from + dump_n) $dumpoff;
            in_byte = stim[t];
            start = 1;
            @(negedge clk);
            start = 0;
            while (!done) @(negedge clk);
            $fwrite(f, "%0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d %0d\n",
                    pred, path, nz0, nz1, nz2, nz3, pr0, pr1, pr2, pr3,
                    tok_cycles, wreads, cyc_engine, cyc_scan, cyc_post, cyc_recall);
        end
        $fclose(f);
        $finish;
    end
endmodule
