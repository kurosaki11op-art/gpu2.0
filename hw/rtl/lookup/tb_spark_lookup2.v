`timescale 1ns/1ps
// Drives bytes from in.hex through spark_lookup2 and writes per byte: pred hit src count bucket conf (hex/decimal).
module tb_spark_lookup2;
    parameter TB = 11;
    parameter N = 1000;
    reg clk = 0, rst = 1, in_valid = 0; reg [7:0] in_byte = 0;
    reg cfg_we = 0; reg [4:0] cfg_addr = 0; reg [7:0] cfg_data = 0;
    wire busy, out_valid, hit; wire [7:0] pred, conf; wire [2:0] src; wire [1:0] count; wire [4:0] bucket;
    spark_lookup2 #(.TB(TB)) dut (clk, rst, in_valid, in_byte, cfg_we, cfg_addr, cfg_data, busy, out_valid, pred, hit, src, count, bucket, conf);
    always #5 clk = ~clk;
    reg [7:0] mem [0:N-1];
    integer i, f;
    initial begin
        $readmemh("in.hex", mem);
        f = $fopen("out2.txt", "w");
        repeat (4) @(posedge clk);
        rst = 0;
        if ($test$plusargs("cfgtest"))           // run-time write of every confidence entry: entry i = (7*i + 3) mod 256
            for (i = 0; i < 32; i = i + 1) begin
                @(posedge clk); cfg_we <= 1; cfg_addr <= i; cfg_data <= (7 * i + 3) & 255;
                @(posedge clk); cfg_we <= 0;
            end
        wait (!busy); @(posedge clk);
        for (i = 0; i < N; i = i + 1) begin
            @(posedge clk); in_byte <= mem[i]; in_valid <= 1; @(posedge clk); in_valid <= 0;
            while (!out_valid) @(posedge clk);
            $fwrite(f, "%02x %0d %0d %0d %0d %0d\n", pred, hit, src, count, bucket, conf);
            wait (!busy);
        end
        $fclose(f);
        $display("DONE %0d", N);
        $finish;
    end
endmodule
