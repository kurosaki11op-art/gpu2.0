// One tile with the OpenRAM macros (-DOPENRAM, AW = 12: 4096 words = 4 macros). After the zero-fill, writes by posted updates (add), reads by lookups;
// checks the byte-masked halves (even and odd word addresses), all four macro banks, accumulation, and saturation at 255.
`timescale 1ns/1ps
module tb_tile_openram;
    parameter AW = 12, FW = 72;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg cv = 0; reg [FW-1:0] cf = 0; wire cr; wire rv; wire [FW-1:0] rf; reg rr = 1;
    wire [4*FW-1:0] z1, z2; wire [3:0] v1, v2;
    l_tile #(0, 0, AW, FW) dut (.clk(clk), .rst(rst), .cl_req_valid(cv), .cl_req_flit(cf), .cl_req_ready(cr), .cl_rsp_valid(rv), .cl_rsp_flit(rf), .cl_rsp_ready(rr),
        .rq_in_flit({4*FW{1'b0}}), .rq_in_valid(4'b0), .rq_in_ready(), .rq_out_flit(z1), .rq_out_valid(v1), .rq_out_ready(4'hF),
        .rp_in_flit({4*FW{1'b0}}), .rp_in_valid(4'b0), .rp_in_ready(), .rp_out_flit(z2), .rp_out_valid(v2), .rp_out_ready(4'hF));
    integer errs = 0, n = 0, i; reg [15:0] expv [0:4095]; reg [11:0] addrs [0:11];
    reg [8:0] t0, t1;
    task send(input [1:0] ty, input [17:0] a, input [31:0] d); begin
        @(negedge clk); cf = {ty, 6'd0, 6'd0, 8'd7, a, d}; cv = 1; @(negedge clk); while (!cr) @(negedge clk); cv = 0; end endtask
    task upd(input [11:0] a, input [7:0] d0, input [7:0] d1); begin
        send(2'd2, a, {16'd0, d1, d0}); t0 = expv[a][7:0] + d0; t1 = expv[a][15:8] + d1;
        expv[a] = {(t1 > 255) ? 8'd255 : t1[7:0], (t0 > 255) ? 8'd255 : t0[7:0]}; end endtask
    task look(input [11:0] a); begin
        send(2'd0, a, 32'd0); @(negedge clk); while (!rv) @(negedge clk);
        n = n + 1; if (rf[15:0] !== expv[a]) begin errs = errs + 1; $display("MISMATCH addr %0d got %h expected %h", a, rf[15:0], expv[a]); end
        @(negedge clk); end endtask
    initial begin
        for (i = 0; i < 4096; i = i + 1) expv[i] = 16'h0000;
        addrs[0] = 0; addrs[1] = 1; addrs[2] = 2; addrs[3] = 511; addrs[4] = 512; addrs[5] = 513; addrs[6] = 1023; addrs[7] = 1024; addrs[8] = 2047; addrs[9] = 2048; addrs[10] = 3000; addrs[11] = 4095;
        repeat (4) @(negedge clk); rst = 0; repeat (4200) @(negedge clk);          // zero-fill of 4096 words
        for (i = 0; i < 12; i = i + 1) look(addrs[i]);                              // all zero after the fill
        for (i = 0; i < 12; i = i + 1) upd(addrs[i], i + 3, 2 * i + 1);
        for (i = 0; i < 12; i = i + 1) upd(addrs[i], 100, 200);                     // second update: the second counter saturates (21+200 > 255 for i >= 10... checked by the model)
        for (i = 0; i < 12; i = i + 1) upd(addrs[i], 100, 100);
        for (i = 0; i < 12; i = i + 1) look(addrs[i]);
        $display("OPENRAM tile: %0d lookups checked, %0d mismatches", n, errs);
        $finish;
    end
endmodule
