// SPARK memories for the SkyWater SKY130 ASIC build.
// spark_bram / spark_spram (FPGA block RAMs) are rebuilt from OpenRAM sky130_sram_2kbyte_1rw1r_32x512_8
// macros: port 0 writes (weight load / recall update), port 1 reads, one-cycle read latency as on the FPGA.
// Depth is split into 512-word banks, width into 32-bit columns. No power-on contents: weights are written
// through the core's ld_* port. spark_ram (small state RAMs) stays in spark_ram_asic.v and becomes flip-flops.
module sram_array #(parameter W = 32, parameter DEPTH = 512, parameter AW = 12) (
    input              clk,
    input              we,
    input  [AW-1:0]    wa,
    input  [W-1:0]     wd,
    input  [AW-1:0]    ra,
    output [W-1:0]     rd
);
    localparam NB = (DEPTH + 511) / 512;          // banks (depth)
    localparam NC = (W + 31) / 32;                // columns (width)
    localparam BW = (NB > 1) ? $clog2(NB) : 1;
    wire [BW-1:0] wbank = (NB > 1) ? wa[AW-1:9] : 0;
    wire [BW-1:0] rbank = (NB > 1) ? ra[AW-1:9] : 0;
    reg  [BW-1:0] rbank_q;
    always @(posedge clk) rbank_q <= rbank;
    wire [NC*32-1:0] wd_pad = {{(NC*32-W){1'b0}}, wd};
    wire [NB*NC*32-1:0] dout;                    // flat: bank b, column c at [(b*NC+c)*32 +: 32]
    genvar b, c;
    generate
        for (b = 0; b < NB; b = b + 1) begin : bank
            for (c = 0; c < NC; c = c + 1) begin : col
                sky130_sram_2kbyte_1rw1r_32x512_8 u_sram (
                    .clk0(clk), .csb0(!(we && wbank == b)), .web0(1'b0), .wmask0(4'hF),
                    .addr0(wa[8:0]), .din0(wd_pad[32*c +: 32]), .dout0(),
                    .clk1(clk), .csb1(!(rbank == b)), .addr1(ra[8:0]), .dout1(dout[(b*NC+c)*32 +: 32]));
            end
        end
    endgenerate
    wire [NC*32-1:0] row = dout[rbank_q*NC*32 +: NC*32];
    assign rd = row[W-1:0];
endmodule

module spark_bram #(parameter W = 64, parameter DEPTH = 16, parameter AW = 4, parameter INIT = "") (
    input clk, input we, input [AW-1:0] wa, input [W-1:0] wd, input [AW-1:0] ra, output [W-1:0] rd);
    sram_array #(.W(W), .DEPTH(DEPTH), .AW(AW)) u (.clk(clk), .we(we), .wa(wa), .wd(wd), .ra(ra), .rd(rd));
endmodule

// single-port on the FPGA; the recall unit never reads and writes in the same cycle, so on silicon
// port 0 takes the writes and port 1 the reads
module spark_spram #(parameter W = 64, parameter DEPTH = 16, parameter AW = 4) (
    input clk, input we, input [AW-1:0] wa, input [W-1:0] wd, input [AW-1:0] ra, output [W-1:0] rd);
    sram_array #(.W(W), .DEPTH(DEPTH), .AW(AW)) u (.clk(clk), .we(we), .wa(wa), .wd(wd), .ra(ra), .rd(rd));
endmodule
