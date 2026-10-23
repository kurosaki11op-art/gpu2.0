// L mesh router: 5 ports (0 local, 1 north, 2 east, 3 south, 4 west), XY routing, one-flit input and output registers, ready/valid.
// Flit (72 bits): {type[1:0], dst[5:0], src[5:0], tag[7:0], addr[17:0], data[31:0]}; dst/src = {y[2:0], x[2:0]}.
`timescale 1ns/1ps
module l_router #(parameter X = 0, Y = 0, FW = 72) (
    input clk, rst,
    input  [5*FW-1:0] in_flit,  input  [4:0] in_valid,  output [4:0] in_ready,
    output [5*FW-1:0] out_flit, output [4:0] out_valid, input  [4:0] out_ready);
    reg [FW-1:0] ib [0:4]; reg [4:0] iv;                       // input registers
    reg [FW-1:0] ob [0:4]; reg [4:0] ov;                       // output registers
    reg [2:0] rr [0:4];
    assign in_ready = ~iv;
    genvar g;
    generate for (g = 0; g < 5; g = g + 1) begin : pk
        assign out_flit[g*FW +: FW] = ob[g]; assign out_valid[g] = ov[g];
    end endgenerate
    // dst field is f[69:64] = {y[2:0], x[2:0]}
    function [2:0] rt; input [FW-1:0] f; reg [2:0] dx, dy; begin
        dx = f[66:64]; dy = f[69:67];
        if (dx > X) rt = 3'd2; else if (dx < X) rt = 3'd4; else if (dy > Y) rt = 3'd3; else if (dy < Y) rt = 3'd1; else rt = 3'd0;
    end endfunction
    integer o, k, i; reg [4:0] taken; reg found; reg [2:0] sel;
    always @(posedge clk) begin
        if (rst) begin iv <= 0; ov <= 0; for (o = 0; o < 5; o = o + 1) rr[o] <= 0; end
        else begin
            taken = 0;
            for (o = 0; o < 5; o = o + 1) begin
                // drain the output register when the neighbour takes it
                if (ov[o] && out_ready[o]) ov[o] <= 1'b0;
                // refill from the winning input if the output register is free or being drained now
                if (!ov[o] || out_ready[o]) begin
                    found = 0; sel = 0;
                    for (k = 0; k < 5; k = k + 1) begin
                        i = (rr[o] + k) % 5;
                        if (!found && iv[i] && !taken[i] && rt(ib[i]) == o) begin found = 1; sel = i; end
                    end
                    if (found) begin ob[o] <= ib[sel]; ov[o] <= 1'b1; taken[sel] = 1'b1; rr[o] <= (sel + 1) % 5; end
                end
            end
            for (i = 0; i < 5; i = i + 1) begin
                if (taken[i]) iv[i] <= 1'b0;
                else if (in_valid[i] && !iv[i]) begin ib[i] <= in_flit[i*FW +: FW]; iv[i] <= 1'b1; end
            end
        end
    end
endmodule
