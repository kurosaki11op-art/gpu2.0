"""28 Oct 2026, SIMULATED error (numpy emulation of each number format, fp64 truth), ESTIMATED energy per multiply (45 nm; fp32 3.7, fp16 1.1, int8 0.2 pJ from Horowitz ISSCC 2014 as references; every other energy is our ASSUMPTION, listed in ENERGY).
ARITHMETIC PRIMITIVE SHOOT-OUT. Each primitive = operand quantiser Q plus optional product perturbation P; a multiply is P(Q(a)*Q(b)); accumulation stays exact (fp64) so only the multiplier is tested. Tasks: dense matmul 128^3, radix-2 FFT n=1024 (twiddle and butterfly multiplies), conjugate gradient on a 2D Poisson 32x32 (dot products and axpy multiplies), Kalman filter 4 states x 2000 steps (all matrix products). Error = relative L2 against the fp64 run; CG reports final residual after 300 iterations and iterations to 1e-6 (inf = never)."""
import numpy as np
rs = np.random.RandomState(0)
def fl(dt): return lambda x: x.astype(dt).astype(np.float64)
def intq(bits):
    def q(x):
        m = np.abs(x).max() + 1e-300; L = 2 ** (bits - 1) - 1; return np.round(x / m * L) / L * m
    return q
def bfp(bits, blk=16):
    def q(x):
        s = x.shape; f = x.reshape(-1); pad = (-len(f)) % blk; f = np.concatenate([f, np.zeros(pad)]).reshape(-1, blk)
        e = np.floor(np.log2(np.abs(f).max(1, keepdims=True) + 1e-300)); sc = 2.0 ** (e - (bits - 2)); r = np.round(f / sc) * sc
        return r.reshape(-1)[:len(x.reshape(-1))].reshape(s)
    return q
def lns(F):
    def q(x):
        a = np.abs(x); out = np.zeros_like(x); nz = a > 1e-300; out[nz] = np.sign(x[nz]) * 2.0 ** (np.round(np.log2(a[nz]) * F) / F); return out
    return q
bf16 = lambda x: (np.ascontiguousarray(x.astype(np.float32)).view(np.uint32) & 0xFFFF0000).view(np.float32).astype(np.float64)
def stoch(N):
    def p(pr, scale):
        u = np.clip(pr / scale, -1, 1); return (u + rs.randn(*u.shape) * np.sqrt(np.maximum(1 - u * u, 0) / N)) * scale
    return p
def analog(rel):
    return lambda pr, scale: pr + rs.randn(*pr.shape) * rel * scale
# name: (quantiser, perturbation or None, assumed pJ per multiply at 45 nm, source of the energy)
P = {
 "fp32": (fl(np.float32), None, 3.7, "Horowitz"), "fp16": (fl(np.float16), None, 1.1, "Horowitz"), "bfloat16": (bf16, None, 1.0, "assumed"),
 "int8": (intq(8), None, 0.2, "Horowitz"), "int4 (16x16 table)": (intq(4), None, 0.05, "assumed (int8 x 1/4)"),
 "block FP 8-bit mantissa": (bfp(8), None, 0.22, "assumed (int8 + exponent logic)"), "block FP 5-bit mantissa": (bfp(5), None, 0.08, "assumed"),
 "log number F=8 (multiply = add)": (lns(8), None, 0.15, "assumed (adder + log-to-linear table)"), "log number F=3": (lns(3), None, 0.10, "assumed"),
 "stochastic N=256 (int8 operands)": (intq(8), stoch(256), 0.20, "assumed (256 gate toggles)"), "stochastic N=4096": (intq(8), stoch(4096), 3.2, "assumed (4096 gate toggles)"),
 "analog 1% noise (int8 operands)": (intq(8), analog(0.01), 0.07, "assumed (cell + amortised converter)"), "analog 5% noise": (intq(8), analog(0.05), 0.07, "assumed"),
}
def make(name):
    q, p, _, _ = P[name]
    def mul(a, b):
        a, b = np.broadcast_arrays(np.asarray(a, np.float64), np.asarray(b, np.float64)); pr = q(a.copy()) * q(b.copy())
        return pr if p is None else p(pr, (np.abs(a).max() * np.abs(b).max() + 1e-300))
    return mul
rel = lambda x, t: np.linalg.norm(x - t) / np.linalg.norm(t)
def matmul(mul, A, B): return mul(A[:, :, None], B[None, :, :]).sum(1)
def fft(mul, x):
    n = len(x); idx = np.arange(n); rev = np.array([int(format(i, "010b")[::-1], 2) for i in idx]); a = x[rev].astype(np.complex128); m = 2
    while m <= n:
        w = np.exp(-2j * np.pi * np.arange(m // 2) / m); a = a.reshape(-1, m); u = a[:, :m // 2]; v = a[:, m // 2:]
        t = mul(v.real, w.real) - mul(v.imag, w.imag) + 1j * (mul(v.real, w.imag) + mul(v.imag, w.real)); a = np.concatenate([u + t, u - t], 1); m *= 2
    return a.reshape(-1)
def cg(mul, n=32, its=300):
    N = n * n; b = rs.randn(N); x = np.zeros(N)
    def Ax(v):
        g = v.reshape(n, n); o = 4 * g.copy(); o[1:] -= g[:-1]; o[:-1] -= g[1:]; o[:, 1:] -= g[:, :-1]; o[:, :-1] -= g[:, 1:]; return o.reshape(-1)
    dot = lambda u, v: mul(u, v).sum(); r = b.copy(); pv = r.copy(); rr = dot(r, r); b0 = np.linalg.norm(b); hit = np.inf
    for k in range(its):
        Ap = Ax(pv); a = rr / dot(pv, Ap); x = x + mul(np.full(N, a), pv); r = r - mul(np.full(N, a), Ap); rn = dot(r, r)
        if np.linalg.norm(r) / b0 < 1e-6 and hit == np.inf: hit = k + 1
        pv = r + mul(np.full(N, rn / rr), pv); rr = rn
    return np.linalg.norm(Ax(x) - b) / b0, hit
def kalman(mul, T=2000):
    mm = lambda A, B: matmul_small(mul, A, B); dt = .1; F = np.array([[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1.]]); H = np.eye(4)[:2]; Q = .01 * np.eye(4); R = .5 * np.eye(2)
    r0 = np.random.RandomState(1); x = np.zeros(4); truth = np.array([0, 0, 1, .5]); xe = np.zeros(4); Pm = np.eye(4); err = []
    for t in range(T):
        truth = F @ truth; z = H @ truth + r0.randn(2) * .7; xe = mm(F, xe[:, None])[:, 0]; Pm = mm(mm(F, Pm), F.T) + Q
        S = mm(mm(H, Pm), H.T) + R; K = mm(mm(Pm, H.T), np.linalg.inv(S)); xe = xe + mm(K, (z - mm(H, xe[:, None])[:, 0])[:, None])[:, 0]; Pm = mm(np.eye(4) - mm(K, H), Pm); err.append(xe)
    return np.array(err)
def matmul_small(mul, A, B): return mul(A[:, :, None], B[None, :, :]).sum(1)
A = rs.randn(128, 128); B = rs.randn(128, 128); sig = rs.randn(1024)
tm, tf = A @ B, np.fft.fft(sig); ex = make("fp32"); ref = None
exact = lambda a, b: np.asarray(a, np.float64) * np.asarray(b, np.float64)
tk = kalman(exact); tc = cg(exact)
print("SIMULATED error vs fp64 (lower is better). CG truth run: final residual %.2e, iterations to 1e-6: %s" % tc)
print("%-34s %9s %9s %11s %12s %9s %10s  %s" % ("primitive", "matmul", "FFT", "CG resid", "CG its", "Kalman", "pJ/mult", "energy source (ESTIMATED)"))
for nm in P:
    mul = make(nm); e1 = rel(matmul(mul, A, B), tm); e2 = rel(fft(mul, sig), tf); r, h = cg(mul); e4 = rel(kalman(mul), tk)
    print("%-34s %9.2e %9.2e %11.2e %12s %9.2e %10.3f  %s" % (nm, e1, e2, r, h, e4, P[nm][2], P[nm][3]), flush=True)
