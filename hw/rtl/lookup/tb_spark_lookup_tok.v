`timescale 1ns/1ps
// For each token of in_tok.hex: DRAFT(K) from the committed history, log the proposals, then LEARN the token.
// Output line per position: "n tok src cnt tok src cnt ..." (hex tokens). Also logs total cycles.
module tb_spark_lookup_tok;
    parameter TB = 12, N = 500, K = 8;
    reg clk = 0, rst = 1, cmd_valid = 0, cmd_op = 0; reg [17:0] cmd_tok = 0; reg [3:0] cmd_k = 0;
    wire busy, d_valid, done; wire [17:0] d_tok; wire [1:0] d_src, d_cnt; wire [3:0] d_n;
    spark_lookup_tok #(.TB(TB)) dut (clk, rst, cmd_valid, cmd_op, cmd_tok, cmd_k, busy, d_valid, d_tok, d_src, d_cnt, done, d_n);
    always #5 clk = ~clk;
    reg [17:0] mem [0:N-1];
    integer i, f, cyc_d, cyc_l;
    always @(posedge clk) if (d_valid) $fwrite(f, " %05x %0d %0d", d_tok, d_src, d_cnt);
    initial begin
        $readmemh("in_tok.hex", mem);
        f = $fopen("out_tok.txt", "w");
        repeat (4) @(posedge clk); rst = 0;
        wait (!busy); @(posedge clk);
        cyc_d = 0; cyc_l = 0;
        for (i = 0; i < N; i = i + 1) begin
            @(posedge clk); cmd_op <= 1; cmd_k <= K; cmd_valid <= 1; @(posedge clk); cmd_valid <= 0;
            while (!done) begin @(posedge clk); cyc_d = cyc_d + 1; end
            $fwrite(f, " | %0d\n", d_n);
            @(posedge clk); cmd_op <= 0; cmd_tok <= mem[i]; cmd_valid <= 1; @(posedge clk); cmd_valid <= 0;
            while (!done) begin @(posedge clk); cyc_l = cyc_l + 1; end
        end
        $fclose(f);
        $display("DONE N=%0d draft_cycles=%0d learn_cycles=%0d", N, cyc_d, cyc_l);
        $finish;
    end
endmodule
