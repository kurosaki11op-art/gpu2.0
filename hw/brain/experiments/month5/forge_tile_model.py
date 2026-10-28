"""28 Oct 2026, SIMULATED. L Forge tile model, part 1: a vectorised emulation of the lane arithmetic that is BIT-EXACT to forge_lane_golden.py (checked here against the scalar golden model, which the RTL matches on 3,288 ops), used to run a matrix product through the lane and measure its error against fp64; plus cycle counts for a tile array. Cycle model (ASSUMED structure): one lane per tile consumes one block pair (16 multiply-accumulates) per cycle; a matrix product C = A B (M x K by K x N) takes M*N*K/16 lane cycles; T tiles share the work evenly."""
import numpy as np, time
from forge_lane_golden import lane_step
def bitlen(x):
    L = np.zeros(x.shape, np.int64); y = x.copy()
    for s in (32, 16, 8, 4, 2, 1): m = y >= (1 << s); L += np.where(m, s, 0); y = np.where(m, y >> s, y)
    return L + (y > 0)
def lane_step_vec(macc, eacc, first, P, E):
    Am = np.where(first, 0, macc); Ae = eacc; zero = Am == 0; ge = E >= Ae; d = np.abs(E - Ae); far = d > 40; dd = np.minimum(d, 40)
    S = np.where(zero, P, np.where(ge, np.where(far, P, (P << dd) + Am), np.where(far, Am, (Am << dd) + P)))
    Es = np.where(zero, E, np.where(ge, np.where(far, E, Ae), np.where(far, Ae, E)))
    sgn = S < 0; mag = np.abs(S); L = bitlen(mag); r = np.maximum(L - 16, 0); mag2 = np.where(r > 0, (mag + (1 << np.maximum(r - 1, 0))) >> r, mag); ov = mag2 >= 65536; mag2 = np.where(ov, mag2 >> 1, mag2); r = np.where(ov, r + 1, r)
    return np.where(sgn, -mag2, mag2), Es + r
def bfp_encode(X, blk=16, mbits=8):
    R, K = X.shape; B = X.reshape(R, K // blk, blk); e = np.floor(np.log2(np.abs(B).max(-1) + 1e-300)).astype(np.int64); sc = 2.0 ** (e - (mbits - 2))[..., None]; lim = 2 ** (mbits - 1) - 1
    return np.clip(np.round(B / sc), -lim, lim).astype(np.int64), e
def lane_matmul(A, B, blk=16):
    ma, ea = bfp_encode(A, blk); mb, eb = bfp_encode(B.T, blk); M, nb = ea.shape; N = mb.shape[0]; macc = np.zeros((M, N), np.int64); eacc = np.zeros((M, N), np.int64)
    for b in range(nb):
        P = ma[:, b, :] @ mb[:, b, :].T; E = ea[:, b][:, None] + eb[:, b][None, :] - 12; macc, eacc = lane_step_vec(macc, eacc, b == 0, P, E)
    return macc * 2.0 ** eacc, M * N * nb
if __name__ == "__main__":
    rs = np.random.RandomState(0)
    # 1. vectorised emulation equals the scalar golden model (which the RTL matches)
    bad = 0
    for trial in range(300):
        nb = rs.randint(1, 17); MA = rs.randint(-127, 128, (nb, 16)); MB = rs.randint(-127, 128, (nb, 16)); EA = rs.randint(-30, 30, nb); EB = rs.randint(-5, 5, nb)
        m, e = 0, 0
        for b in range(nb): m, e = lane_step(m, e, b == 0, MA[b], MB[b], int(EA[b]), int(EB[b]))
        vm = np.zeros(1, np.int64); ve = np.zeros(1, np.int64)
        for b in range(nb): vm, ve = lane_step_vec(vm, ve, b == 0, np.array([int(MA[b] @ MB[b])]), np.array([int(EA[b]) + int(EB[b]) - 12]))
        bad += (int(vm[0]) != m or int(ve[0]) != e)
    print("vectorised lane vs scalar golden: %d mismatches in 300 random sequences" % bad)
    # 2. matrix products through the lane
    rel = lambda x, t: np.linalg.norm(x - t) / np.linalg.norm(t)
    for name, (A, B) in {"normal": (rs.randn(128, 256), rs.randn(256, 128)), "heavy-tailed": (rs.standard_t(2, (128, 256)), rs.standard_t(2, (256, 128)))}.items():
        t0 = time.time(); C, ops = lane_matmul(A, B); print("matmul 128x256x128, %s data: error vs fp64 %.2e, block ops %d, lane cycles on 1 tile %d, on 1,024 tiles %d  [%.1fs]" % (name, rel(C, A @ B), ops, ops, -(-ops // 1024), time.time() - t0))
