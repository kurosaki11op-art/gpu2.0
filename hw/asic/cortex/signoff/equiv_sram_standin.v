// stand-in for the OpenRAM macro: every output bit is the XOR of all input bits, so any difference at a macro input shows up downstream
module sky130_sram_2kbyte_1rw1r_32x512_8 (input clk0, csb0, web0, input [3:0] wmask0, input [8:0] addr0, input [31:0] din0, output [31:0] dout0,
                                          input clk1, csb1, input [8:0] addr1, output [31:0] dout1);
  wire x = ^{clk0, csb0, web0, wmask0, addr0, din0, clk1, csb1, addr1};
  assign dout0 = {32{x}}; assign dout1 = {32{~x}};
endmodule
