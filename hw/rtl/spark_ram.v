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

// Same as spark_ram, but asks synthesis to use dedicated block RAM (BSRAM).
module spark_bram #(
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
    (* ram_style = "block" *) reg [W-1:0] mem [0:DEPTH-1];
    integer i;
    initial begin
        if (INIT != "") $readmemh(INIT, mem);
        else for (i = 0; i < DEPTH; i = i + 1) mem[i] = {W{1'b0}};
    end
    always @(posedge clk) begin
        if (we) mem[wa] <= wd;
        rd <= mem[ra];
    end
endmodule

// Single-port block RAM: one address used for either a write or a read each
// cycle (the recall unit never reads and writes in the same cycle).
module spark_spram #(
    parameter W = 64,
    parameter DEPTH = 16,
    parameter AW = 4
) (
    input              clk,
    input              we,
    input  [AW-1:0]    wa,
    input  [W-1:0]     wd,
    input  [AW-1:0]    ra,
    output reg [W-1:0] rd
);
    (* ram_style = "block" *) reg [W-1:0] mem [0:DEPTH-1];
    wire [AW-1:0] a = we ? wa : ra;
    integer i;
    initial for (i = 0; i < DEPTH; i = i + 1) mem[i] = {W{1'b0}};
    always @(posedge clk) begin
        if (we) mem[a] <= wd;
        rd <= mem[a];
    end
endmodule
