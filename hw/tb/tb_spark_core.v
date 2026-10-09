`timescale 1ns/1ps
// Feeds stim.hex bytes through spark_core one token at a time and writes
// one result line per token to rtl_out.txt:
//   pred path nz0 nz1 nz2 nz3 pr0 pr1 pr2 pr3 tok_cycles wreads engine scan post recall
// Config via plusargs: +sparse= +delta= +exit= +exit_th= +recall= +conf_th= +rmode= +arb_th= +cap= +n=
module tb_spark_core;
    reg clk = 0, rst = 1, start = 0;
    reg [7:0] in_byte = 0;
    integer sparse_en = 1, delta_en = 0, exit_en = 0, exit_th = 64, recall_en = 0,
            conf_th = 1, rmode = 0, arb_th = 64, cap = 0, adapt = 0, thr = 0, n = 0, a = 230, acc_sh = 2, s_sh = 4;
    reg [7:0] stim [0:65535];
    integer t, f;
    wire done; wire [7:0] pred; wire [1:0] path;
    wire [31:0] tok_cycles, wreads, cyc_engine, cyc_scan, cyc_post, cyc_recall;
    wire [15:0] nz0, nz1, nz2, nz3, pr0, pr1, pr2, pr3;

    spark_core dut (
        .clk(clk), .rst(rst), .start(start), .in_byte(in_byte),
        .sparse_en(sparse_en[0]), .delta_en(delta_en[0]), .exit_en(exit_en[0]),
        .recall_en(recall_en[0]), .cap(cap[15:0]), .recall_mode(rmode[1:0]), .arb_th(arb_th[15:0]), .exit_th(exit_th),
        .conf_th(conf_th[1:0]), .cfg_a(a[8:0]), .acc_sh(acc_sh[3:0]), .s_sh(s_sh[3:0]), .adapt_en(adapt[0]), .thr_en(thr[0]),
        .ld_we(1'b0), .ld_sel(3'd0), .ld_addr(11'd0), .ld_data(64'd0),
        .done(done), .pred(pred), .path(path), .tok_cycles(tok_cycles), .wreads(wreads),
        .cyc_engine(cyc_engine), .cyc_scan(cyc_scan), .cyc_post(cyc_post),
        .cyc_recall(cyc_recall),
        .nz0(nz0), .nz1(nz1), .nz2(nz2), .nz3(nz3), .pr0(pr0), .pr1(pr1), .pr2(pr2), .pr3(pr3)
    );

    always #5 clk = ~clk;   // 100 MHz simulation clock (timing is not modelled)

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
        $readmemh("stim.hex", stim);
        f = $fopen("rtl_out.txt", "w");
        repeat (3) @(posedge clk);
        rst = 0;
        @(posedge clk);
        for (t = 0; t < n; t = t + 1) begin
            @(negedge clk);
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
