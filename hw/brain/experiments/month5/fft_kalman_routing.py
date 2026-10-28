"""28 Oct 2026, SIMULATED accuracy (numpy emulation of number formats, fp64 truth), ESTIMATED traffic proxy. L FORGE PRECISION ROUTING for the FFT and the Kalman filter (difference D2 of docs/L_forge_design.md). Founder asked to proceed without waiting; this is one autonomous step.
PART 1, FFT: (a) a standalone radix-2 FFT (n = 1024 complex) with data rounded to a block floating-point format after every stage (block of 16, shared exponent, m mantissa bits), twiddles rounded the same way; error against numpy's fp64 FFT versus m; (b) the FFT used as the INNER solver of a refinement loop: periodic screened Poisson (L + 0.01 I) x = b on a 64 x 64 grid solved spectrally in low precision (2D FFT, multiply by the rounded reciprocal of the eigenvalue, inverse FFT), outer fp64 residual with the stencil, target 1e-12.
PART 2, Kalman: 12-state, 6-measurement random stable system, 1000 steps, 3 seeds. Matrix products use rounded operands, wide accumulation, rounded result. Variants route which stages stay fp64: all low; covariance update fp64; covariance fully fp64 (predict and update); Joseph form low. Error = relative L2 difference of the estimate against the fp64 filter; also min eigenvalue of P and share of flops in fp64."""
import numpy as np
def bfp(bits, blk=16):
    def q(x):
        s = x.shape; f = x.reshape(-1); pad = (-len(f)) % blk; f = np.concatenate([f, np.zeros(pad)]).reshape(-1, blk)
        e = np.floor(np.log2(np.abs(f).max(1, keepdims=True) + 1e-300)); sc = 2.0 ** (e - (bits - 2)); r = np.round(f / sc) * sc
        return r.reshape(-1)[:x.size].reshape(s)
    return q
def fl(dt): return lambda x: x.astype(dt).astype(np.float64)
def bf16(x): return (np.ascontiguousarray(x.astype(np.float32)).view(np.uint32) & 0xFFFF0000).view(np.float32).astype(np.float64)
def intq(bits):
    def q(x): m = np.abs(x).max() + 1e-300; L = 2 ** (bits - 1) - 1; return np.round(x / m * L) / L * m
    return q
ID = lambda x: x
def fft_last(xr, xi, Q):
    n = xr.shape[-1]; lg = int(np.log2(n)); rev = np.array([int(format(i, "0%db" % lg)[::-1], 2) for i in range(n)]); ar = xr[..., rev]; ai = xi[..., rev]; lead = xr.shape[:-1]; m = 2
    while m <= n:
        sh = lead + (n // m, m); ar = ar.reshape(sh); ai = ai.reshape(sh); k = np.arange(m // 2); wr = Q(np.cos(2 * np.pi * k / m)); wi = Q(-np.sin(2 * np.pi * k / m))
        ur, vr, ui, vi = ar[..., :m // 2], ar[..., m // 2:], ai[..., :m // 2], ai[..., m // 2:]; tr = vr * wr - vi * wi; ti = vr * wi + vi * wr
        ar = Q(np.concatenate([ur + tr, ur - tr], -1)).reshape(lead + (n,)); ai = Q(np.concatenate([ui + ti, ui - ti], -1)).reshape(lead + (n,)); m *= 2
    return ar, ai
def fft2_q(xr, xi, Q, inverse=False):
    if inverse: xr, xi = xi, xr
    ar, ai = fft_last(xr, xi, Q); ar, ai = np.swapaxes(ar, 0, 1), np.swapaxes(ai, 0, 1); ar, ai = fft_last(ar, ai, Q); ar, ai = np.swapaxes(ar, 0, 1), np.swapaxes(ai, 0, 1)
    return (ai, ar) if inverse else (ar, ai)
print("PART 1a: standalone FFT n=1024, relative L2 error vs fp64 (rounded after every stage, SIMULATED)")
rs = np.random.RandomState(0); x = rs.randn(1024) + 1j * rs.randn(1024); ref = np.fft.fft(x)
for nm, Q in (("BFP5", bfp(5)), ("BFP8", bfp(8)), ("BFP10", bfp(10)), ("BFP12", bfp(12)), ("BFP16", bfp(16)), ("BFP24", bfp(24)), ("int8", intq(8)), ("fp16", fl(np.float16)), ("bfloat16", bf16), ("fp32", fl(np.float32))):
    yr, yi = fft_last(x.real.copy(), x.imag.copy(), Q); print("  %-9s %.2e" % (nm, np.linalg.norm(yr + 1j * yi - ref) / np.linalg.norm(ref)))
print("\nPART 1b: FFT as the inner solver of a refinement loop (screened Poisson 64x64, periodic, target 1e-12)")
n = 64; sig = 0.01; kk = np.arange(n); lam = 4 - 2 * np.cos(2 * np.pi * kk)[:, None] / 1.0 if False else (4 - 2 * np.cos(2 * np.pi * kk / n)[:, None] - 2 * np.cos(2 * np.pi * kk / n)[None, :]) + sig
def A64(v): return 4 * v - np.roll(v, 1, 0) - np.roll(v, -1, 0) - np.roll(v, 1, 1) - np.roll(v, -1, 1) + sig * v
b = np.random.RandomState(1).randn(n, n); b0 = np.linalg.norm(b)
def spectral(r, Q):
    fr, fi = fft2_q(r, np.zeros_like(r), Q); inv = Q(1.0 / lam); gr, gi = Q(fr * inv), Q(fi * inv); dr, di = fft2_q(gr, gi, Q, inverse=True); return dr / (n * n)
x0 = np.fft.ifft2(np.fft.fft2(b) / lam).real; print("  fp64 spectral solve, single shot: residual %.1e" % (np.linalg.norm(b - A64(x0)) / b0))
print("  %-9s %6s %10s %10s" % ("format", "outer", "final", "converged"))
for nm, Q in (("BFP5", bfp(5)), ("BFP8", bfp(8)), ("BFP12", bfp(12)), ("int8", intq(8)), ("fp16", fl(np.float16)), ("bfloat16", bf16)):
    x = np.zeros((n, n)); outer = 0
    for outer in range(1, 61):
        r = b - A64(x)
        if np.linalg.norm(r) / b0 < 1e-12: outer -= 1; break
        s = 2.0 ** (-np.ceil(np.log2(np.abs(r).max()))); x = x + spectral(r * s, Q) / s
    fin = np.linalg.norm(b - A64(x)) / b0; print("  %-9s %6d %10.1e %10s" % (nm, outer, fin, "yes" if fin < 1e-12 else "NO"), flush=True)
print("\nPART 2: Kalman filter, 12 states, 6 measurements, 1000 steps, 3 seeds; error = relative L2 difference of the estimates vs the fp64 filter")
def mm(A, B, Q): return Q(Q(A) @ Q(B))
FL = {"predictP": 3456, "S": 1296, "K": 1512, "x": 144, "updP": 2592}
def kalman(seed, Qp, Qs, Qk, Qx, Qu, joseph=False, T=1000):
    r = np.random.RandomState(seed); n, m = 12, 6; Qr, _ = np.linalg.qr(r.randn(n, n)); F = 0.98 * Qr; H = r.randn(m, n) / np.sqrt(n); Qc = 0.01 * np.eye(n); R = 0.5 * np.eye(m)
    truth = r.randn(n); x = np.zeros(n); P = np.eye(n); est = []; mn = np.inf; rz = np.random.RandomState(seed + 100)
    for t in range(T):
        truth = F @ truth + rz.randn(n) * 0.1; z = H @ truth + rz.randn(m) * np.sqrt(0.5)
        x = mm(F, x[:, None], Qx)[:, 0]; P = mm(mm(F, P, Qp), F.T, Qp) + Qc; P = Qp(0.5 * (P + P.T))
        S = mm(mm(H, P, Qs), H.T, Qs) + R; K = mm(mm(P, H.T, Qk), np.linalg.inv(S), Qk)
        x = x + mm(K, (z - mm(H, x[:, None], Qx)[:, 0])[:, None], Qx)[:, 0]; IKH = np.eye(n) - mm(K, H, Qu)
        P = mm(mm(IKH, P, Qu), IKH.T, Qu) + mm(mm(K, R, Qu), K.T, Qu) if joseph else mm(IKH, P, Qu); P = Qu(0.5 * (P + P.T)); mn = min(mn, np.linalg.eigvalsh(P).min()); est.append(x.copy())
    return np.array(est), mn
FMTS = {"BFP8": bfp(8), "int8": intq(8), "bfloat16": bf16, "fp16": fl(np.float16), "fp32": fl(np.float32)}
print("%-9s %-34s %10s %12s %12s" % ("format", "routing (what stays fp64)", "error", "min eig P", "fp64 flops"))
ref = {s: kalman(s, ID, ID, ID, ID, ID) for s in range(3)}
for nm, Qf in FMTS.items():
    for lab, sel, jo in (("nothing (all low)", (Qf, Qf, Qf, Qf, Qf), False), ("covariance update fp64", (Qf, Qf, Qf, Qf, ID), False), ("covariance predict+update fp64", (ID, Qf, Qf, Qf, ID), False), ("Joseph form, all low", (Qf, Qf, Qf, Qf, Qf), True), ("Joseph, update fp64", (Qf, Qf, Qf, Qf, ID), True)):
        errs = []; mins = []
        for s in range(3):
            e, mn = kalman(s, *sel, joseph=jo); errs.append(np.linalg.norm(e - ref[s][0]) / np.linalg.norm(ref[s][0])); mins.append(mn)
        share = (FL["updP"] * (sel[4] is ID) + FL["predictP"] * (sel[0] is ID)) / sum(FL.values()); print("%-9s %-34s %10.2e %12.2e %11.0f%%" % (nm, lab, np.mean(errs), np.min(mins), 100 * share), flush=True)
