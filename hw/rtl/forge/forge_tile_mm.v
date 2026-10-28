// L Forge tile, matrix-product microprogram (28 Oct 2026, SIMULATED/verified): block memories A (M*NB words) and B (N*NB words), one block per word
// ({block exponent 8 bits, 16 signed 8-bit mantissas}), one forge_lane, an address generator and an output memory C (macc, eacc per element).
// C(i,j) = sum over blocks b of the lane operation on A(i,b) and B(j,b); one block operation (16 multiply-accumulates) per cycle once the pipeline is full.
module forge_tile_mm #(parameter M = 16, N = 16, NB = 8) (
    input clk, input rst, input start, output reg busy, output reg done, output reg [31:0] cycles,
    input [$clog2(M*N)-1:0] c_raddr, output reg signed [16:0] c_macc, output reg signed [11:0] c_eacc);
    reg [135:0] mema [0:M*NB-1]; reg [135:0] memb [0:N*NB-1]; reg signed [16:0] cm [0:M*N-1]; reg signed [11:0] ce [0:M*N-1];
    initial begin $readmemh("mm_a.hex", mema); $readmemh("mm_b.hex", memb); end
    reg [15:0] i, j, b; reg run; reg [135:0] wa, wb; reg v1, f1, l1; reg [15:0] i1, j1; reg v2, l2; reg [15:0] i2, j2;
    wire signed [16:0] macc; wire signed [11:0] eacc; wire ov;
    forge_lane lane (.clk(clk), .rst(rst), .valid(v1), .first(f1), .ma(wa[127:0]), .mb(wb[127:0]), .ea(wa[135:128]), .eb(wb[135:128]), .macc(macc), .eacc(eacc), .out_valid(ov));
    always @(posedge clk) begin
        if (rst) begin busy <= 0; done <= 0; run <= 0; v1 <= 0; v2 <= 0; cycles <= 0; end
        else begin
            done <= 0; c_macc <= cm[c_raddr]; c_eacc <= ce[c_raddr];
            if (busy) cycles <= cycles + 1;
            if (start && !busy) begin busy <= 1; run <= 1; i <= 0; j <= 0; b <= 0; cycles <= 0; end
            // stage 0: issue the addresses (registered read of both memories)
            wa <= mema[i * NB + b]; wb <= memb[j * NB + b]; v1 <= run; f1 <= (b == 0); l1 <= (b == NB - 1); i1 <= i; j1 <= j;
            if (run) begin
                if (b == NB - 1) begin b <= 0; if (j == N - 1) begin j <= 0; if (i == M - 1) run <= 0; else i <= i + 1; end else j <= j + 1; end else b <= b + 1;
            end
            // stage 1 -> lane (registered result, available one cycle later); stage 2: capture the last block's result
            v2 <= v1 && l1; i2 <= i1; j2 <= j1;
            if (v2) begin cm[i2 * N + j2] <= macc; ce[i2 * N + j2] <= eacc; end
            if (!run && !v1 && !v2 && busy && !(v2)) begin busy <= 0; done <= 1; end
        end
    end
endmodule
