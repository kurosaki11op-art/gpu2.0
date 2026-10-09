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
        if (INIT != "") $readmemh(INIT, mem);
        else for (i = 0; i < DEPTH; i = i + 1) mem[i] = {W{1'b0}};
        rd = {W{1'b0}};
    end
    always @(posedge clk) begin
        if (we) mem[wa] <= wd;
        rd <= mem[ra];
    end
endmodule
