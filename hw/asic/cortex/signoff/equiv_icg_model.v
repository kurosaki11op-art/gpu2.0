module sky130_fd_sc_hd__dlclkp_1 (input CLK, input GATE, output GCLK);
  reg q; always @(CLK or GATE) if (!CLK) q = GATE;
  assign GCLK = CLK & q;
endmodule
