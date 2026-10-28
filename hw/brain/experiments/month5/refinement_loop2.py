"""28 Oct 2026, SIMULATED accuracy and iteration counts, ESTIMATED traffic proxy. L FORGE REFINEMENT LOOP, round 2: (1) bigger inner iteration cap, (2) a multigrid preconditioner built only from stencil operations (weighted Jacobi smoothing, full-weighting restriction, bilinear interpolation: adds and shifts, no multiplier beyond block-scaled constants), run in the low-precision format, (3) fp16 fix: scale the inner residual by a power of two so its largest entry lies in (0.5, 1] and unscale the correction (the round-1 fp16 stall at 7e-8 is the fp16 subnormal floor 6e-8, an underflow of small corrections, not a precision limit).
Grids 31, 63, 127 (vertex-centred multigrid needs 2^k - 1). Target 1e-12. Traffic proxy: vector passes x bytes per element; fp64 CG iteration 10 passes, outer step 8 passes (fp64), low-precision CG iteration 10 passes, multigrid-preconditioned CG iteration 29 passes (10 + about 19 for one V-cycle with one pre and one post smoothing sweep, coarse levels 4/3 of the fine level)."""
import os, numpy as np
from multiprocessing import Pool
def fl(dt): return lambda x: x.astype(dt).astype(np.float64)
def bf16(x): return (np.ascontiguousarray(x.astype(np.float32)).view(np.uint32) & 0xFFFF0000).view(np.float32).astype(np.float64)
def intq(bits):
    def q(x): m = np.abs(x).max() + 1e-300; L = 2 ** (bits - 1) - 1; return np.round(x / m * L) / L * m
    return q
def bfp(bits, blk=16):
    def q(x):
        s = x.shape; f = x.reshape(-1); pad = (-len(f)) % blk; f = np.concatenate([f, np.zeros(pad)]).reshape(-1, blk)
        e = np.floor(np.log2(np.abs(f).max(1, keepdims=True) + 1e-300)); sc = 2.0 ** (e - (bits - 2)); r = np.round(f / sc) * sc
        return r.reshape(-1)[:x.size].reshape(s)
    return q
FMT = {"fp16": (fl(np.float16), 2.0), "bfloat16": (bf16, 2.0), "int8": (intq(8), 1.0), "BFP8": (bfp(8), 1.0625), "BFP5": (bfp(5), 0.6875)}
def L(g):
    o = 4 * g; o[1:] -= g[:-1]; o[:-1] -= g[1:]; o[:, 1:] -= g[:, :-1]; o[:, :-1] -= g[:, 1:]; return o
def restrict(f):
    n = f.shape[0]; p = np.zeros((n + 2, n + 2)); p[1:-1, 1:-1] = f; c = (n - 1) // 2; i = np.arange(c) * 2 + 1
    I, J = np.meshgrid(i, i, indexing="ij"); I = I + 1 - 1; v = 4 * p[I + 1, J + 1]
    v = v + 2 * (p[I, J + 1] + p[I + 2, J + 1] + p[I + 1, J] + p[I + 1, J + 2]) + (p[I, J] + p[I, J + 2] + p[I + 2, J] + p[I + 2, J + 2]); return v / 16.0
def prolong(ec, n):
    c = ec.shape[0]; p = np.zeros((c + 2, c + 2)); p[1:-1, 1:-1] = ec; e = np.zeros((n, n))
    e[1::2, 1::2] = ec; e[0::2, 1::2] = 0.5 * (p[:-1, 1:-1] + p[1:, 1:-1]); e[1::2, 0::2] = 0.5 * (p[1:-1, :-1] + p[1:-1, 1:])
    e[0::2, 0::2] = 0.25 * (p[:-1, :-1] + p[1:, :-1] + p[:-1, 1:] + p[1:, 1:]); return e
_coarse = {}
def coarse_solve(r):
    n = r.shape[0]
    if n not in _coarse:
        N = n * n; A = np.zeros((N, N))
        for k in range(N): e = np.zeros(N); e[k] = 1; A[:, k] = L(e.reshape(n, n)).reshape(-1)
        _coarse[n] = np.linalg.inv(A)
    return (_coarse[n] @ r.reshape(-1)).reshape(n, n)
def vcycle(r, Q, w=0.8):
    n = r.shape[0]
    if n <= 3: return Q(coarse_solve(r))
    x = Q(w / 4 * r); res = Q(r - L(x)); rc = Q(4 * restrict(res)); ec = vcycle(rc, Q, w); x = Q(x + prolong(ec, n)); return Q(x + w / 4 * Q(r - L(x)))
def cg64(A, b, tol, mx=4000):
    x = np.zeros_like(b); r = b.copy(); p = r.copy(); rr = r @ r; b0 = np.linalg.norm(b)
    for k in range(mx):
        Ap = A(p); a = rr / (p @ Ap); x += a * p; r -= a * Ap; rn = r @ r
        if np.sqrt(rn) / b0 < tol: return k + 1
        p = r + rn / rr * p; rr = rn
    return mx
def inner(n, r0, Q, tol, cap, mg):
    A = lambda v: Q(L(v.reshape(n, n)).reshape(-1)); M = (lambda v: Q(vcycle(v.reshape(n, n), Q)).reshape(-1)) if mg else (lambda v: v)
    d = np.zeros_like(r0); r = Q(r0.copy()); z = M(r); p = z.copy(); rz = r @ z; r00 = np.linalg.norm(r) + 1e-300
    for k in range(cap):
        Ap = A(p); den = p @ Ap
        if not np.isfinite(den) or den <= 0: return d, k
        a = rz / den; d = Q(d + a * p); r = Q(r - a * Ap)
        if np.linalg.norm(r) / r00 < tol: return d, k + 1
        z = M(r); rzn = r @ z; p = Q(z + rzn / rz * p); rz = rzn
    return d, cap
def run(job):
    n, variant, fmt = job; Q, by = FMT[fmt]; mg = variant.startswith("MG"); cap = {"CG cap60": 60, "CG cap250": 250, "MG-PCG cap30": 30}[variant]; passes = 29 if mg else 10
    rs = np.random.RandomState(0); N = n * n; b = rs.randn(N); A64 = lambda v: L(v.reshape(n, n)).reshape(-1); b0 = np.linalg.norm(b); k64 = cg64(A64, b, 1e-12); t64 = k64 * 10 * 8.0
    x = np.zeros(N); outer = 0; tot = 0
    for outer in range(1, 61):
        r = b - A64(x)
        if np.linalg.norm(r) / b0 < 1e-12: outer -= 1; break
        s = 2.0 ** (-np.ceil(np.log2(np.abs(r).max()))); d, k = inner(n, r * s, Q, 1e-2, cap, mg); tot += k; x = x + d / s
    fin = np.linalg.norm(b - A64(x)) / b0; hi = (outer + 1) * 8 * 8.0; lo = tot * passes * by
    return (n, variant, fmt, outer, tot, fin, fin < 1e-12, (hi + lo) / t64, hi / (hi + lo), k64)
if __name__ == "__main__":
    jobs = []
    for n in (31, 63, 127):
        for fmt in FMT:
            jobs.append((n, "CG cap60", fmt)); jobs.append((n, "MG-PCG cap30", fmt))
        for fmt in ("fp16", "int8", "BFP8"): jobs.append((n, "CG cap250", fmt))
    with Pool(os.cpu_count()) as pool: res = pool.map(run, jobs, chunksize=1)
    print("REFINEMENT LOOP round 2 (scaled inner residual): target 1e-12; traffic vs plain fp64 CG (proxy)")
    print("%-5s %-14s %-9s %6s %7s %9s %9s %9s %9s %9s" % ("grid", "variant", "format", "outer", "inner", "final", "converged", "traffic", "fp64 share", "fp64 CG its"))
    for r in sorted(res, key=lambda r: (r[0], r[1], list(FMT).index(r[2]))): print("%-5d %-14s %-9s %6d %7d %9.1e %9s %9.2f %8.0f%% %9d" % (r[0], r[1], r[2], r[3], r[4], r[5], "yes" if r[6] else "NO", r[7], 100 * r[8], r[9]))
