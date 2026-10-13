`timescale 1ns/1ps
// Drives bytes from in.hex through spark_lookup and writes one line per byte to out.txt: pred hit order count (hex).
module tb_spark_lookup;
    parameter TB = 12;
    parameter N = 1000;
    reg clk = 0, rst = 1, in_valid = 0; reg [7:0] in_byte = 0;
    wire busy, out_valid, hit; wire [7:0] pred; wire [1:0] order_idx, count;
    spark_lookup #(TB) dut (clk, rst, in_valid, in_byte, busy, out_valid, pred, hit, order_idx, count);
    always #5 clk = ~clk;
    reg [7:0] mem [0:N-1];
    integer i, f, cyc, total;
    initial begin
        $readmemh("in.hex", mem);
        f = $fopen("out.txt", "w");
        // hash unit test: print a few CRC values for comparison with zlib
        $display("CRC %h %h %h", dut.crc6(48'h0000_0000_6261, 32'd1), dut.crc6(48'h0123_4567_89AB, 32'd4), dut.crc6(48'hFFFF_FFFF_FFFF, 32'd3));
        repeat (4) @(posedge clk);
        rst = 0;
        total = 0;
        wait (!busy); @(posedge clk);
        for (i = 0; i < N; i = i + 1) begin
            @(posedge clk); in_byte <= mem[i]; in_valid <= 1; @(posedge clk); in_valid <= 0;
            cyc = 1;
            while (!out_valid) begin @(posedge clk); cyc = cyc + 1; end
            $fwrite(f, "%02x %0d %0d %0d\n", pred, hit, order_idx, count);
            total = total + cyc;
            wait (!busy);
        end
        $fclose(f);
        $display("DONE bytes=%0d avg_cycles_per_byte(incl. handshake)=%0f", N, total * 1.0 / N);
        $finish;
    end
endmodule
