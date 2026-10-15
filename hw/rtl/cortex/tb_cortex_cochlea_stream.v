// Testbench: N clips (smp.hex) streamed sample by sample into cortex_cochlea_stream; pixels to out_coch.txt.
`timescale 1ns/1ps
module tb_cortex_cochlea_stream;
    parameter N = 2, ALIGN = 0, LEAD = 4;
    reg clk = 0, rst = 1; always #5 clk = ~clk;
    reg start = 0, smp_valid = 0; reg [15:0] smp_data = 0;
    wire smp_ready, busy, done, px_we; wire [9:0] px_addr; wire [7:0] px_data;
    cortex_cochlea_stream #(.ALIGN(ALIGN), .LEAD(LEAD)) dut(.clk(clk), .rst(rst), .start(start), .smp_valid(smp_valid), .smp_data(smp_data),
        .smp_ready(smp_ready), .busy(busy), .done(done), .px_we(px_we), .px_addr(px_addr), .px_data(px_data));
    reg [15:0] mem [0:N*16000-1];
    integer f, c, q, t0;
    always @(posedge clk) if (px_we) $fwrite(f, " %0d", px_data);
    initial begin
        $readmemh("smp.hex", mem); f = $fopen("out_coch.txt", "w");
        repeat (3) @(negedge clk); rst = 0;
        for (c = 0; c < N; c = c + 1) begin
            @(negedge clk); start = 1; t0 = $time; @(negedge clk); start = 0;
            q = 0;
            while (!done) begin
                if (smp_ready && q < 16000) begin smp_valid = 1; smp_data = mem[c * 16000 + q]; q = q + 1; end
                else smp_valid = 0;
                @(negedge clk);
            end
            smp_valid = 0; @(negedge clk);
            $fwrite(f, "\n"); if (c == 0) $display("cycles per clip %0d", ($time - t0) / 10);
        end
        $fclose(f); $finish;
    end
endmodule
