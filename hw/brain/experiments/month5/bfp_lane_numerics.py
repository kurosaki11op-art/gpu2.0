"""28 Oct 2026, SIMULATED (numpy emulation, fp64 truth). L FORGE block floating-point multiply-accumulate lane: how many mantissa bits, what block size, what accumulator width and what rounding. A lane multiplies two blocks of m-bit signed mantissas that share one exponent per block (exact integer products, exact integer sum inside a block), then adds the block sums across the reduction dimension into an accumulator that keeps A mantissa bits (floating-point style, round to nearest after each block add). Matrix product 64 x 256 by 256 x 64 with random normal entries (and a heavy-tailed variant), relative Frobenius error against fp64. Questions: (1) does the accumulator need to be wider than the operands, (2) block size 8, 16, 32, 64, (3) round-to-nearest versus truncation when forming the mantissas, (4) shared exponent with outliers (heavy-tailed data)."""
import numpy as np
def to_blocks(X, mbits, blk, rnd):
    """X: (R, K) -> mantissas (int) (R, K/blk, blk) and exponents (R, K/blk): value = mant * 2^(e - (mbits - 2))."""
    R, K = X.shape; B = X.reshape(R, K // blk, blk); e = np.floor(np.log2(np.abs(B).max(-1) + 1e-300)); sc = 2.0 ** (e - (mbits - 2))[..., None]
    q = B / sc; mant = np.round(q) if rnd else np.trunc(q); lim = 2 ** (mbits - 1) - 1; return np.clip(mant, -lim, lim), sc[..., 0]
def round_mant(v, abits):
    if abits >= 53: return v
    m, e = np.frexp(v); return np.ldexp(np.round(m * 2 ** abits) / 2 ** abits, e)
def lane_matmul(A, B, mbits, blk, abits, rnd=True):
    ma, sa = to_blocks(A, mbits, blk, rnd); mb, sb = to_blocks(B.T, mbits, blk, rnd)                    # B transposed: reduce along K
    nb = ma.shape[1]; out = np.zeros((A.shape[0], B.shape[1]))
    for b in range(nb):
        blocksum = (ma[:, b, :] @ mb[:, b, :].T) * (sa[:, b][:, None] * sb[:, b][None, :])               # exact integer dot inside the block (products and sum exact), scaled by the block exponents
        out = round_mant(out + blocksum, abits)
    return out
rs = np.random.RandomState(0); M, K, N = 64, 256, 64
data = {"normal": (rs.randn(M, K), rs.randn(K, N)), "heavy-tailed": (rs.standard_t(2, (M, K)), rs.standard_t(2, (K, N)))}
rel = lambda x, t: np.linalg.norm(x - t) / np.linalg.norm(t)
for dn, (A, B) in data.items():
    ref = A @ B; print("\n== %s data ==" % dn)
    print("(1) accumulator mantissa bits, block 16, round to nearest:")
    print("    %-8s" % "mant" + " ".join("acc%-3d" % a for a in (8, 11, 16, 24, 53)))
    for mb in (4, 5, 6, 8, 10, 12): print("    %-8s" % ("m=%d" % mb) + " ".join("%.1e" % rel(lane_matmul(A, B, mb, 16, a), ref) for a in (8, 11, 16, 24, 53)))
    print("(2) block size, m=8, acc24:   " + "  ".join("blk%d %.1e" % (b, rel(lane_matmul(A, B, 8, b, 24), ref)) for b in (8, 16, 32, 64)))
    print("(3) rounding, m=8, blk16, acc24: nearest %.1e | truncate %.1e" % (rel(lane_matmul(A, B, 8, 16, 24, True), ref), rel(lane_matmul(A, B, 8, 16, 24, False), ref)))
