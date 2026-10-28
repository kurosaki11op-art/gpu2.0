"""28 Oct 2026, SIMULATED accuracy and iteration counts (numpy emulation of number formats), ESTIMATED traffic proxy. L FORGE REFINEMENT LOOP (precision routing, difference D2 of docs/L_forge_design.md). Problem: 2D Poisson A x = b (5-point stencil, N = n*n unknowns, random b), target relative residual 1e-12 (fp64 accuracy). Method: mixed-precision iterative refinement: OUTER loop in fp64 (true residual r = b - A x, update x += d); INNER solve A d = r by conjugate gradient in a low-precision format (every stored vector, the matvec result and each update is rounded to the format; dot products use exact accumulation of rounded operands) until the inner residual drops by 1e-2 or 60 iterations. Baseline: fp64 CG to 1e-12.
Formats: fp16, bfloat16, int8 (per-vector scale), block floating point with 8-bit mantissa and shared exponent over 16 values (BFP8), BFP5. Traffic proxy (ESTIMATED): vector passes per iteration (CG iteration 10 passes, outer step 8 passes) x bytes per element (fp64 8; fp16, bfloat16 2; int8 1; BFP8 1.0625; BFP5 0.6875)."""
import numpy as np
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
def make_A(n):
    def Ax(v):
        g = v.reshape(n, n); o = 4 * g; o[1:] -= g[:-1]; o[:-1] -= g[1:]; o[:, 1:] -= g[:, :-1]; o[:, :-1] -= g[:, 1:]; return o.reshape(-1)
    return Ax
def cg64(Ax, b, tol, mx=2000):
    x = np.zeros_like(b); r = b.copy(); p = r.copy(); rr = r @ r; b0 = np.linalg.norm(b)
    for k in range(mx):
        Ap = Ax(p); a = rr / (p @ Ap); x += a * p; r -= a * Ap; rn = r @ r
        if np.sqrt(rn) / b0 < tol: return x, k + 1
        p = r + rn / rr * p; rr = rn
    return x, mx
def cg_low(Ax, r0, Q, tol, mx):
    d = np.zeros_like(r0); r = Q(r0.copy()); p = r.copy(); rr = r @ r; r00 = np.sqrt(rr) + 1e-300
    for k in range(mx):
        Ap = Q(Ax(p)); den = p @ Ap
        if den <= 0 or not np.isfinite(den): return d, k
        a = rr / den; d = Q(d + a * p); r = Q(r - a * Ap); rn = r @ r
        if np.sqrt(rn) / r00 < tol: return d, k + 1
        p = Q(r + rn / rr * p); rr = rn
    return d, mx
def refine(Ax, b, Q, target=1e-12, inner_tol=1e-2, inner_max=60, outer_max=60):
    x = np.zeros_like(b); b0 = np.linalg.norm(b); inner = 0; outer = 0; hist = []
    for outer in range(1, outer_max + 1):
        r = b - Ax(x); rel = np.linalg.norm(r) / b0; hist.append(rel)
        if rel < target: outer -= 1; break
        d, k = cg_low(Ax, r, Q, inner_tol, inner_max); inner += k; x = x + d
    r = b - Ax(x); return x, outer, inner, np.linalg.norm(r) / b0
print("REFINEMENT LOOP on 2D Poisson, target relative residual 1e-12; baseline fp64 CG")
print("%-5s %-9s %7s %7s %8s %9s %12s %14s" % ("grid", "format", "outer", "inner", "final", "converged", "traffic vs fp64", "high-precision share of traffic"))
rs = np.random.RandomState(0)
for n in (32, 64, 128):
    N = n * n; Ax = make_A(n); b = rs.randn(N); x64, k64 = cg64(Ax, b, 1e-12); t64 = k64 * 10 * 8.0
    print("%-5d %-9s %7s %7d %8.1e %9s %12.2f %14s" % (n, "fp64 CG", "-", k64, np.linalg.norm(b - Ax(x64)) / np.linalg.norm(b), "yes", 1.0, "100%"))
    for nm, (Q, by) in FMT.items():
        x, outer, inner, fin = refine(Ax, b, Q); conv = fin < 1e-12; hi = outer * 8 * 8.0 + 8 * 8.0; lo = inner * 10 * by; tr = (hi + lo) / t64
        print("%-5d %-9s %7d %7d %8.1e %9s %12.2f %13.0f%%" % (n, nm, outer, inner, fin, "yes" if conv else "NO", tr, 100 * hi / (hi + lo)), flush=True)
