// spark_ram only (small state RAMs -> flip-flops on the ASIC); block RAMs are in spark_mem_sky130.v
// Simple synchronous RAM/ROM: one write port, one registered read port.
// Infers block RAM on FPGAs. INIT = hex file to preload (weights), else zeros.
module spark_ram #(
    parameter W = 64,
    parameter DEPTH = 16,
    parameter AW = 4,
    parameter INIT = ""
) (
    input              clk,
    input              we,
    input  [AW-1:0]    wa,
    input  [W-1:0]     wd,
    input  [AW-1:0]    ra,
    output reg [W-1:0] rd
);
    reg [W-1:0] mem [0:DEPTH-1];
    integer i;
    initial begin
        if (INIT != "") $readmemh(INIT, mem);   // ROM contents (thresholds); RAMs start unknown, as on silicon
    end
    always @(posedge clk) begin
        if (we) mem[wa] <= wd;
        rd <= mem[ra];
    end
endmodule

