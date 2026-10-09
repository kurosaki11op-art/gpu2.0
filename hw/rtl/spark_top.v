// Synthesis top for a fixed trained model: neuron constants (decay, shifts) are
// fixed at build time, so the synthesiser removes the variable shifters and
// multipliers. Runtime switches (sparse/delta/exit/recall/adapt/cap) stay live.
module spark_top (
    input         clk, rst, start,
    input  [7:0]  in_byte,
    input         sparse_en, delta_en, exit_en, recall_en, adapt_en,
    input  [15:0] cap,
    input  [31:0] exit_th,
    input  [1:0]  conf_th,
    input         ld_we,
    input  [2:0]  ld_sel,
    input  [10:0] ld_addr,
    input  [63:0] ld_data,
    output        done,
    output [7:0]  pred,
    output [1:0]  path,
    output [31:0] tok_cycles
);
    wire [31:0] wreads, ce, cs, cp, cr;
    wire [15:0] a0, a1, a2, a3, b0, b1, b2, b3;
    spark_core u (
        .clk(clk), .rst(rst), .start(start), .in_byte(in_byte),
        .sparse_en(sparse_en), .delta_en(delta_en), .exit_en(exit_en), .recall_en(recall_en),
        .cap(cap), .exit_th(exit_th), .conf_th(conf_th),
        .cfg_a(9'd230), .acc_sh(4'd2), .s_sh(4'd4), .adapt_en(adapt_en),
        .ld_we(ld_we), .ld_sel(ld_sel), .ld_addr(ld_addr), .ld_data(ld_data),
        .done(done), .pred(pred), .path(path), .tok_cycles(tok_cycles), .wreads(wreads),
        .cyc_engine(ce), .cyc_scan(cs), .cyc_post(cp), .cyc_recall(cr),
        .nz0(a0), .nz1(a1), .nz2(a2), .nz3(a3), .pr0(b0), .pr1(b1), .pr2(b2), .pr3(b3)
    );
endmodule
