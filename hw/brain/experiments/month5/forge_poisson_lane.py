"""28 Oct 2026, SIMULATED. L Forge refinement loop with the inner solver's DOT PRODUCTS computed by the bit-exact lane arithmetic (blocks of 16, 8-bit mantissas, 16-bit floating accumulator) instead of exact accumulation; storage rounding in BFP8 as in refinement_loop2.py; multigrid V-cycle preconditioner from stencil operations; outer residual in fp64; target 1e-12. Compares outer steps and final residual with the exact-dot run of refinement_loop2."""
import numpy as np
import refinement_loop2 as R
from forge_tile_model import lane_step_vec, bfp_encode
def lane_dot(u, v):
    pad = (-len(u)) % 16
    if pad: u = np.concatenate([u, np.zeros(pad)]); v = np.concatenate([v, np.zeros(pad)])
    mu, eu = bfp_encode(u[None, :]); mv, ev = bfp_encode(v[None, :]); m = np.zeros(1, np.int64); e = np.zeros(1, np.int64)
    for b in range(mu.shape[1]): m, e = lane_step_vec(m, e, b == 0, np.array([int((mu[0, b] * mv[0, b]).sum())]), np.array([int(eu[0, b]) + int(ev[0, b]) - 12]))
    return float(m[0] * 2.0 ** e[0])
def inner_lane(n, r0, Q, tol, cap):
    A = lambda v: Q(R.L(v.reshape(n, n)).reshape(-1)); M = lambda v: Q(R.vcycle(v.reshape(n, n), Q)).reshape(-1)
    d = np.zeros_like(r0); r = Q(r0.copy()); z = M(r); p = z.copy(); rz = lane_dot(r, z); r00 = np.sqrt(abs(lane_dot(r, r))) + 1e-300
    for k in range(cap):
        Ap = A(p); den = lane_dot(p, Ap)
        if not np.isfinite(den) or den <= 0: return d, k
        a = rz / den; d = Q(d + a * p); r = Q(r - a * Ap)
        if np.sqrt(abs(lane_dot(r, r))) / r00 < tol: return d, k + 1
        z = M(r); rzn = lane_dot(r, z); p = Q(z + rzn / rz * p); rz = rzn
    return d, cap
Q = R.FMT["BFP8"][0]
for n in (31, 63):
    N = n * n; b = np.random.RandomState(0).randn(N); A64 = lambda v: R.L(v.reshape(n, n)).reshape(-1); b0 = np.linalg.norm(b); x = np.zeros(N); tot = 0
    for outer in range(1, 61):
        r = b - A64(x)
        if np.linalg.norm(r) / b0 < 1e-12: outer -= 1; break
        s = 2.0 ** (-np.ceil(np.log2(np.abs(r).max()))); d, k = inner_lane(n, r * s, Q, 1e-2, 30); tot += k; x = x + d / s
    print("grid %d: lane dot products: %d outer steps, %d inner iterations, final residual %.1e (exact-dot BFP8 run: %s)" % (n, outer, tot, np.linalg.norm(b - A64(x)) / b0, {31: "9 outer, 27 inner", 63: "10 outer, 30 inner"}[n]), flush=True)
