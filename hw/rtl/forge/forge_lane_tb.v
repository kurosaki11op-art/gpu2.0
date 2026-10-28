// Testbench for forge_lane: vectors in lane_vec.txt (first ea eb ma mb exp_macc exp_eacc), compares after every op.
`timescale 1ns/1ps
module forge_lane_tb;
    reg clk = 0, rst = 1, valid = 0, first = 0; reg [127:0] ma, mb; reg signed [7:0] ea, eb; wire signed [16:0] macc; wire signed [11:0] eacc; wire ov;
    forge_lane dut (.clk(clk), .rst(rst), .valid(valid), .first(first), .ma(ma), .mb(mb), .ea(ea), .eb(eb), .macc(macc), .eacc(eacc), .out_valid(ov));
    always #5 clk = ~clk; integer f, n, bad, r, fi; reg [127:0] hma, hmb; integer iea, ieb, em, ee; reg [31:0] fl;
    initial begin
        f = $fopen("lane_vec.txt", "r"); bad = 0; n = 0; repeat (3) @(posedge clk); rst = 0;
        while (!$feof(f)) begin
            r = $fscanf(f, "%d %d %d %h %h %d %d\n", fi, iea, ieb, hma, hmb, em, ee);
            if (r == 7) begin
                @(negedge clk); first = fi; ea = iea; eb = ieb; ma = hma; mb = hmb; valid = 1; @(negedge clk); valid = 0; @(negedge clk);
                if (macc !== em || eacc !== ee) begin bad = bad + 1; if (bad < 6) $display("MISMATCH op %0d: got %0d %0d expected %0d %0d", n, macc, eacc, em, ee); end
                n = n + 1;
            end
        end
        $display("LANE ops %0d mismatches %0d", n, bad); $finish;
    end
endmodule
