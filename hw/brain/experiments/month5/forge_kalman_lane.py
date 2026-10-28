"""28 Oct 2026, SIMULATED. The 12-state Kalman filter of fft_kalman_routing.py with EVERY matrix product computed by the bit-exact L Forge lane arithmetic (block floating point, 8-bit mantissas, blocks of 16 along the reduction dimension padded with zeros, accumulator of 16 mantissa bits), against the fp64 filter and the truth. Everything else (additions, the 6 x 6 inverse) is fp64 here: the inverse would run on the high-precision path."""
import numpy as np
from forge_tile_model import lane_matmul
def mm(A, B):
    K = A.shape[1]; pad = (-K) % 16
    if pad: A = np.concatenate([A, np.zeros((A.shape[0], pad))], 1); B = np.concatenate([B, np.zeros((pad, B.shape[1]))], 0)
    return lane_matmul(A, B)[0]
def kal(seed, mmf, T=1000):
    r = np.random.RandomState(seed); n, m = 12, 6; Qr, _ = np.linalg.qr(r.randn(n, n)); F = 0.98 * Qr; H = r.randn(m, n) / np.sqrt(n); Qc = 0.01 * np.eye(n); R = 0.5 * np.eye(m)
    truth = r.randn(n); x = np.zeros(n); P = np.eye(n); rz = np.random.RandomState(seed + 100); est = []; err = []
    for t in range(T):
        truth = F @ truth + rz.randn(n) * 0.1; z = H @ truth + rz.randn(m) * np.sqrt(0.5)
        x = mmf(F, x[:, None])[:, 0]; P = mmf(mmf(F, P), F.T) + Qc; P = 0.5 * (P + P.T); S = mmf(mmf(H, P), H.T) + R; K = mmf(mmf(P, H.T), np.linalg.inv(S))
        x = x + mmf(K, (z - mmf(H, x[:, None])[:, 0])[:, None])[:, 0]; P = mmf(np.eye(n) - mmf(K, H), P); P = 0.5 * (P + P.T); est.append(x.copy()); err.append(np.linalg.norm(x - truth))
    return np.array(est), np.sqrt(np.mean(np.square(err[100:])))
ex = lambda A, B: A @ B
res = []
for s in range(3):
    e64, r64 = kal(s, ex); el, rl = kal(s, mm); res.append((np.linalg.norm(el - e64) / np.linalg.norm(e64), r64, rl))
print("Kalman 12 states, all matrix products through the Forge lane (3 seeds): difference from the fp64 filter %s ; RMSE vs truth: fp64 %.3f, lane %.3f" % (["%.2e" % r[0] for r in res], np.mean([r[1] for r in res]), np.mean([r[2] for r in res])))
