// Clock gate: gclk follows clk in cycles where en (sampled while clk is low) is 1. Synthesis for SKY130 (CG_SKY130)
// uses the library's integrated clock-gating cell; simulation uses the equivalent latch + AND.
module cortex_cg (input wire clk, input wire en, output wire gclk);
`ifdef CG_SKY130
    sky130_fd_sc_hd__dlclkp_1 u_icg (.CLK(clk), .GATE(en), .GCLK(gclk));
`else
    reg l = 1'b0;
    always @(clk or en) if (!clk) l = en;
    assign gclk = clk & l;
`endif
endmodule
