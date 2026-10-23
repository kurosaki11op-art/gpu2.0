// L token sequencer (first hardware version): for one byte it walks the 8 binary steps of the counting language model. For each step it forms the
// 6 table slots (context orders 0..5) with a MULTIPLIER-FREE hash (shifts, rotates, XOR), sends the 6 lookups into the mesh, waits for the 6 replies and
// adds the log-odds  ln(n1 + 0.2) - ln(n0 + 0.2)  from a 256-entry ROM (fixed point, 8 fractional bits); the step result is the sum s (signed 16 bits) and
// the target bit. Slot s lives on tile (s mod 16) at local address s / 16. Flit format as in l_tile.v. Word = {n1[7:0], n0[7:0]}.
`timescale 1ns/1ps
module l_seq #(parameter MYX = 0, MYY = 0, NX = 4, FW = 72) (
    input clk, rst,
    input start, input [7:0] tgt, input [7:0] b1, b2, b3, b4, b5,          // b1 = previous byte ... b5 = five bytes back (255 if none)
    output reg busy, output reg done,
    output reg step_valid, output reg signed [15:0] step_s, output reg step_bit,
    output reg req_valid, output reg [FW-1:0] req_flit, input req_ready,
    input rsp_valid, input [FW-1:0] rsp_flit, output rsp_ready);
    reg [7:0] hist [1:5];
    reg [63:0] h [0:5];
    reg signed [15:0] lut [0:255]; initial $readmemh("ln_lut.hex", lut);
    function [63:0] xs; input [63:0] a; reg [63:0] x; begin x = a; x = x ^ (x << 13); x = x ^ (x >> 7); x = x ^ (x << 17); xs = x; end endfunction
    function [63:0] ctxhash; input [2:0] j; input [7:0] c1, c2, c3, c4, c5; reg [63:0] x; reg [7:0] c; integer i; begin
        x = 64'h9E3779B97F4A7C15 ^ ({61'd0, j} << 33) ^ ({61'd0, j} << 7);
        for (i = 0; i < 5; i = i + 1) if (i < j) begin
            c = (i == 0) ? c1 : (i == 1) ? c2 : (i == 2) ? c3 : (i == 3) ? c4 : c5;
            x = x ^ {56'd0, c}; x = {x[58:0], x[63:59]}; x = xs(x);
        end
        ctxhash = x; end endfunction
    function [21:0] slot; input [63:0] hh; input [8:0] node; reg [63:0] y; begin
        y = hh ^ ({55'd0, node} << 20) ^ ({55'd0, node} << 47); y = xs(y); y = y ^ (y >> 31); slot = y[21:0]; end endfunction
    localparam S_IDLE = 0, S_SEND = 1, S_WAIT = 2;
    reg [1:0] st; reg [2:0] j; reg [3:0] got; reg [3:0] step; reg [8:0] node; reg [7:0] tg; reg signed [15:0] acc, acc_n; reg [3:0] got_n;
    wire [21:0] sl = slot(h[j], node);
    wire [3:0] own = sl[3:0];
    assign rsp_ready = 1'b1;
    wire [7:0] rn0 = rsp_flit[7:0], rn1 = rsp_flit[15:8];
    wire signed [15:0] dl = lut[rn1] - lut[rn0];
    integer k;
    always @(posedge clk) begin
        step_valid <= 1'b0; done <= 1'b0;
        if (rst) begin st <= S_IDLE; busy <= 1'b0; req_valid <= 1'b0; got <= 4'd0; acc <= 16'sd0; end
        else begin
            acc_n = acc; got_n = got;
            if (rsp_valid && st != S_IDLE) begin acc_n = acc + dl; got_n = got + 1'b1; end         // replies are taken in any state
            case (st)
                S_IDLE: begin
                    if (start) begin
                        busy <= 1'b1; tg <= tgt; node <= 9'd1; step <= 4'd7; j <= 3'd0; acc <= 16'sd0; got <= 4'd0;
                        for (k = 0; k <= 5; k = k + 1) h[k] <= ctxhash(k[2:0], b1, b2, b3, b4, b5);
                        st <= S_SEND;
                    end
                end
                S_SEND: begin
                    acc <= acc_n; got <= got_n;
                    if (!req_valid || req_ready) begin
                        if (j < 6) begin
                            req_flit <= {2'd0, 1'b0, own[3:2], 1'b0, own[1:0], MYY[2:0], MYX[2:0], 5'd0, j, sl[21:4], 32'd0};
                            req_valid <= 1'b1; j <= j + 1'b1;
                        end else begin req_valid <= 1'b0; st <= S_WAIT; end
                    end
                end
                S_WAIT: begin
                    if (got_n == 4'd6) begin
                        step_valid <= 1'b1; step_s <= acc_n; step_bit <= tg[step];
                        node <= {node[7:0], tg[step]}; got <= 4'd0; acc <= 16'sd0; j <= 3'd0;
                        if (step == 4'd0) begin st <= S_IDLE; busy <= 1'b0; done <= 1'b1; end else begin step <= step - 1'b1; st <= S_SEND; end
                    end else begin acc <= acc_n; got <= got_n; end
                end
                default: st <= S_IDLE;
            endcase
        end
    end
endmodule
