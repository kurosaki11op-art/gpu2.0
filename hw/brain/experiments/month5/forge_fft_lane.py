"""28 Oct 2026, SIMULATED. FFT through the bit-exact L Forge lane: small DFTs computed as real matrix products (the DFT matrix [Fr -Fi; Fi Fr] times [xr; xi]) so that the lane stays full, and a two-word split for more precision on the 8-bit lane: each operand is x = xh + xl with xh and xl both rounded to 8-bit blocks, and a product costs three lane passes (xh*wh + xh*wl + xl*wh), giving about 16 mantissa bits. Compares the error against numpy's fp64 FFT for 1 pass (plain 8-bit) and 3 passes, N = 64 and a four-step N = 256 (two 16-point DFT stages plus twiddles in fp64), and counts lane block operations."""
import numpy as np
from forge_tile_model import lane_matmul
def dft_real(n): k = np.arange(n); W = np.exp(-2j * np.pi * np.outer(k, k) / n); return np.block([[W.real, -W.imag], [W.imag, W.real]])
def q8(X):                                  # nearest 8-bit block rounding of a matrix along its rows (blocks of 16), used for the split
    from forge_tile_model import bfp_encode
    m, e = bfp_encode(X); return (m * (2.0 ** (e - 6))[..., None]).reshape(X.shape)
def mm(A, B, passes):
    if passes == 1: return lane_matmul(A, B)[0], lane_matmul(A, B)[1]
    Ah = q8(A); Al = q8(A - Ah); Bh = q8(B.T).T; Bl = q8((B - Bh).T).T
    c1, o1 = lane_matmul(Ah, Bh); c2, o2 = lane_matmul(Ah, Bl); c3, o3 = lane_matmul(Al, Bh); return c1 + c2 + c3, o1 + o2 + o3
rs = np.random.RandomState(0); rel = lambda x, t: np.linalg.norm(x - t) / np.linalg.norm(t)
print("N = 64, batch 64 complex vectors, DFT as one real 128 x 128 matrix product:")
n = 64; F = dft_real(n); X = rs.randn(n, 64) + 1j * rs.randn(n, 64); XR = np.vstack([X.real, X.imag]); ref = np.fft.fft(X, axis=0)
for passes in (1, 3):
    C, ops = mm(F, XR, passes); Y = C[:n] + 1j * C[n:]; print("  %d lane pass(es): error %.2e, block operations %d (a radix-2 FFT would need about %d multiply-accumulates per vector: %d block ops at full lane use)" % (passes, rel(Y, ref), ops, n // 2 * 6 * 4, 64 * (n // 2) * 6 * 4 // 16))
print("N = 256 four-step (16 x 16): 16-point DFT stages as matrix products, twiddles in fp64 (a real design would use the lane's high-precision path):")
n1 = 16; F1 = dft_real(n1); N = 256; x = rs.randn(N, 32) + 1j * rs.randn(N, 32); ref = np.fft.fft(x, axis=0); w = np.exp(-2j * np.pi * np.outer(np.arange(16), np.arange(16)) / N)
for passes in (1, 3):
    ops = 0; Y = np.zeros((N, 32), complex)
    A = x.reshape(16, 16, 32)                       # index n = 16*a + b  (a = n1 index, b = n2 index): first DFT over a for each b
    T = np.zeros((16, 16, 32), complex)
    for b in range(16):
        blk = A[:, b, :]; C, o = mm(F1, np.vstack([blk.real, blk.imag]), passes); ops += o; T[:, b, :] = C[:16] + 1j * C[16:]
    T = T * w[:, :, None]                           # twiddle factors W_N^(k1*b)
    for k1 in range(16):
        blk = T[k1, :, :]; C, o = mm(F1, np.vstack([blk.real, blk.imag]), passes); ops += o; Y[k1::16, :] = C[:16] + 1j * C[16:]
    print("  %d lane pass(es): error %.2e, block operations %d for 32 transforms of 256 points" % (passes, rel(Y, ref), ops))
