// Testbench for cortex_look: look_in.hex = per case: threshold, known mask, C scores of A, C scores of B (20-bit fields). Writes "pred look" per case to look_out.txt.
`timescale 1ns/1ps
module tb_look;
    parameter NCASE = 100, C = 10, SW = 20;
    reg [C*SW-1:0] sa, sb; reg [C-1:0] known; reg [SW:0] th; wire [3:0] pred; wire look;
    cortex_look #(.C(C), .SW(SW)) dut(.sa(sa), .sb(sb), .known(known), .th(th), .pred(pred), .look(look));
    reg [31:0] mem [0:NCASE * (2 * C + 2)]; integer f, n, c, p;
    initial begin
        $readmemh("look_in.hex", mem); f = $fopen("look_out.txt", "w"); p = 0;
        for (n = 0; n < NCASE; n = n + 1) begin
            th = mem[p]; known = mem[p + 1]; p = p + 2;
            for (c = 0; c < C; c = c + 1) begin sa[c*SW +: SW] = mem[p]; p = p + 1; end
            for (c = 0; c < C; c = c + 1) begin sb[c*SW +: SW] = mem[p]; p = p + 1; end
            #1; $fdisplay(f, "%0d %0d", pred, look);
        end
        $fclose(f); $display("cases %0d", NCASE); $finish;
    end
endmodule
