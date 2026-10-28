"""28 Oct 2026, SIMULATED. Integer golden model of the L Forge block floating-point lane (hw/rtl/forge/forge_lane.v) and its test-vector generator. One op: a block of 16 signed 8-bit mantissa pairs with block exponents ea, eb; P = sum of products (exact integer); value P * 2^(ea+eb-12); added into a floating accumulator (macc signed, magnitude below 2^16, exponent eacc) with round-to-nearest, ties away from zero; exponent gaps above 40 bits keep the larger operand. Also provides lane_dot() used by the tile model."""
import os, random
import numpy as np
def lane_step(macc, eacc, first, ma, mb, ea, eb):
    P = int(sum(int(a) * int(b) for a, b in zip(ma, mb))); E = ea + eb - 12; Am = 0 if first else macc; Ae = eacc
    if Am == 0: S, Es = P, E
    elif E >= Ae:
        d = E - Ae; S, Es = (P, E) if d > 40 else ((P << d) + Am, Ae)
    else:
        d = Ae - E; S, Es = (Am, Ae) if d > 40 else ((Am << d) + P, E)
    sgn = S < 0; mag = -S if sgn else S; L = mag.bit_length()
    if L <= 16: return S, Es
    r = L - 16; mag = (mag + (1 << (r - 1))) >> r
    if mag >= 65536: mag >>= 1; r += 1
    return (-mag if sgn else mag), Es + r
def lane_dot(MA, EA, MB, EB):
    """MA, MB: (nblocks, 16) int mantissas; EA, EB: (nblocks,) block exponents; returns the lane's accumulated value as float."""
    m, e = 0, 0
    for b in range(len(EA)): m, e = lane_step(m, e, b == 0, MA[b], MB[b], int(EA[b]), int(EB[b]))
    return m * 2.0 ** e
if __name__ == "__main__":
    rnd = random.Random(1); out = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "rtl", "forge"))
    lines = []; m, e = 0, 0
    for seq in range(400):
        n = rnd.randint(1, 16); base = rnd.randint(-20, 20); wide = rnd.random() < 0.2
        for b in range(n):
            kind = rnd.random(); ma = [rnd.randint(-127, 127) if kind > 0.1 else rnd.choice([0, 0, 1, -1, 127, -127]) for _ in range(16)]; mb = [rnd.randint(-127, 127) for _ in range(16)]
            ea = base + (rnd.randint(-60, 60) if wide else rnd.randint(-3, 3)); eb = rnd.randint(-5, 5); first = 1 if b == 0 else 0
            m, e = lane_step(m, e, first, ma, mb, max(-127, min(127, ea)), eb)
            hx = lambda v: "".join("%02x" % (x & 255) for x in v[::-1])
            lines.append("%d %d %d %s %s %d %d" % (first, max(-127, min(127, ea)), eb, hx(ma), hx(mb), m, e))
    open(os.path.join(out, "lane_vec.txt"), "w").write("\n".join(lines) + "\n"); print("wrote", len(lines), "ops to", os.path.join(out, "lane_vec.txt"))
