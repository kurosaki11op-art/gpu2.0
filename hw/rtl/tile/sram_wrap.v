// Memory-agnostic bank for the L tile. Fixed ports: one synchronous read port (read data valid the cycle after re) and one write port,
// 16-bit words (two 8-bit counters), 2^AW words. Three builds with the same ports:
//   default      : behavioural model (simulation, any size)
//   -DOPENRAM    : the open SKY130 OpenRAM macro sky130_sram_2kbyte_1rw1r_32x512_8 (32 x 512; two 16-bit words per row, byte-masked write),
//                  split into 512-row banks, each port clock gated by its own select (cortex_cg), as in the Cortex ASIC build
//   a foundry compiler, gain-cell eDRAM or non-volatile memory: replace the body of this module only; the tile does not change
`timescale 1ns/1ps
module sram_wrap #(parameter AW = 12) (
    input clk,
    input re, input [AW-1:0] ra, output [15:0] rdata,
    input we, input [AW-1:0] wa, input [15:0] wd);
`ifdef OPENRAM
    localparam ROWS = 1 << (AW - 1);              // 32-bit rows, two words each
    localparam NBK = (ROWS + 511) / 512;
    localparam BW = (NBK > 1) ? $clog2(NBK) : 1;
    wire [AW-2:0] rrow = ra[AW-1:1], wrow = wa[AW-1:1];
    wire [BW-1:0] rbank = (NBK > 1) ? rrow[AW-2:9] : {BW{1'b0}}, wbank = (NBK > 1) ? wrow[AW-2:9] : {BW{1'b0}};
    reg [BW-1:0] rbank_q; reg rhalf_q;
    always @(posedge clk) begin rbank_q <= rbank; rhalf_q <= ra[0]; end
    wire [32*NBK-1:0] dout;
    genvar b;
    generate for (b = 0; b < NBK; b = b + 1) begin : bank
        wire wsel = we && (wbank == b), rsel = re && (rbank == b);
        wire ck0, ck1;
        cortex_cg g0 (.clk(clk), .en(wsel), .gclk(ck0));
        cortex_cg g1 (.clk(clk), .en(rsel), .gclk(ck1));
        sky130_sram_2kbyte_1rw1r_32x512_8 u_sram (
            .clk0(ck0), .csb0(!wsel), .web0(1'b0), .wmask0(wa[0] ? 4'b1100 : 4'b0011), .addr0(wrow[8:0]), .din0({wd, wd}), .dout0(),
            .clk1(ck1), .csb1(!rsel), .addr1(rrow[8:0]), .dout1(dout[32*b +: 32]));
    end endgenerate
    wire [31:0] row = dout[32*rbank_q +: 32];
    assign rdata = rhalf_q ? row[31:16] : row[15:0];
`else
    reg [15:0] mem [0:(1 << AW) - 1]; reg [15:0] q; integer ii;
    initial for (ii = 0; ii < (1 << AW); ii = ii + 1) mem[ii] = ii * 40503 + (ii >> 3);
    always @(posedge clk) begin if (re) q <= mem[ra]; if (we) mem[wa] <= wd; end
    assign rdata = q;
`endif
endmodule
