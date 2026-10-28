// L Forge block floating-point multiply-accumulate lane (28 Oct 2026, SIMULATED/verified against forge_lane_golden.py).
// One block of 16 signed 8-bit mantissa pairs (ma, mb) with block exponents ea, eb per cycle: exact integer dot product P, scaled by 2^(ea+eb-12),
// added into a floating accumulator (a zero block sum leaves the accumulator unchanged) (signed 16-bit-magnitude mantissa macc, exponent eacc) with round-to-nearest (ties away from zero) after the add.
// value = macc * 2^eacc. 'first' starts a new sum. Operand alignment is exact up to 40 bits; a larger exponent gap keeps the larger operand.
module forge_lane (
    input clk, input rst, input valid, input first,
    input [127:0] ma, input [127:0] mb, input signed [7:0] ea, input signed [7:0] eb,
    output reg signed [16:0] macc, output reg signed [11:0] eacc, output reg out_valid);
    integer i; reg signed [19:0] P; reg signed [11:0] E; reg signed [11:0] Ae; reg signed [16:0] Am;
    reg signed [63:0] S; reg signed [63:0] Ps, As; integer d, dd, L, r; reg [63:0] mag; reg sgn; reg signed [11:0] Es;
    always @(posedge clk) begin
        out_valid <= 0;
        if (rst) begin macc <= 0; eacc <= 0; end
        else if (valid) begin
            P = 0; for (i = 0; i < 16; i = i + 1) P = P + $signed(ma[8*i +: 8]) * $signed(mb[8*i +: 8]);
            E = ea + eb - 12; Am = first ? 17'sd0 : macc; Ae = eacc;
            if (Am == 0) begin S = P; Es = E; end
            else if (P == 0) begin S = Am; Es = Ae; end
            else begin
                if (E >= Ae) begin d = E - Ae; if (d > 40) begin S = P; Es = E; end else begin Ps = P; S = (Ps <<< d) + Am; Es = Ae; end end
                else begin d = Ae - E; if (d > 40) begin S = Am; Es = Ae; end else begin As = Am; S = (As <<< d) + P; Es = E; end end
            end
            sgn = S < 0; mag = sgn ? -S : S; L = 0; for (i = 0; i < 64; i = i + 1) if (mag[i]) L = i + 1;
            if (L <= 16) begin macc <= S; eacc <= Es; end
            else begin
                r = L - 16; mag = (mag + (64'd1 << (r - 1))) >> r;
                if (mag >= 64'd65536) begin mag = mag >> 1; r = r + 1; end
                macc <= sgn ? -$signed(mag[16:0]) : $signed(mag[16:0]); eacc <= Es + r;
            end
            out_valid <= 1;
        end
    end
endmodule
