"""28 Oct 2026, SIMULATED. The 12-state Kalman filter with EVERY operation that is a product, including the 6 x 6 matrix inverse, on the bit-exact L Forge lane: the inverse of the innovation covariance S is computed by Newton-Schulz iteration X <- X (2I - S X) (matrix products only), started from X0 = S^T / (||S||_1 ||S||_inf) and run for a fixed number of iterations (ITERS), so no high-precision inverse path is needed. Additions and the starting scale are fp64 here (additions would be on the add path). Compared with the fp64 filter and the truth."""
import numpy as np
from forge_kalman_lane import mm
ITERS = 8
def inv_ns(S):
    X = S.T / (np.abs(S).sum(0).max() * np.abs(S).sum(1).max()); I2 = 2 * np.eye(len(S))
    for _ in range(ITERS): X = mm(X, I2 - mm(S, X))
    return X
def kal(seed, mmf, invf, T=1000):
    r = np.random.RandomState(seed); n, m = 12, 6; Qr, _ = np.linalg.qr(r.randn(n, n)); F = 0.98 * Qr; H = r.randn(m, n) / np.sqrt(n); Qc = 0.01 * np.eye(n); R = 0.5 * np.eye(m)
    truth = r.randn(n); x = np.zeros(n); P = np.eye(n); rz = np.random.RandomState(seed + 100); est = []; err = []; ierr = []
    for t in range(T):
        truth = F @ truth + rz.randn(n) * 0.1; z = H @ truth + rz.randn(m) * np.sqrt(0.5)
        x = mmf(F, x[:, None])[:, 0]; P = mmf(mmf(F, P), F.T) + Qc; P = 0.5 * (P + P.T); S = mmf(mmf(H, P), H.T) + R; Si = invf(S); ierr.append(np.linalg.norm(Si @ S - np.eye(m)))
        K = mmf(mmf(P, H.T), Si); x = x + mmf(K, (z - mmf(H, x[:, None])[:, 0])[:, None])[:, 0]; P = mmf(np.eye(n) - mmf(K, H), P); P = 0.5 * (P + P.T); est.append(x.copy()); err.append(np.linalg.norm(x - truth))
    return np.array(est), np.sqrt(np.mean(np.square(err[100:]))), np.mean(ierr)
ex = lambda A, B: A @ B; res = []
for s in range(3):
    e64, r64, _ = kal(s, ex, np.linalg.inv); el, rl, ie = kal(s, mm, inv_ns); res.append((np.linalg.norm(el - e64) / np.linalg.norm(e64), r64, rl, ie))
print("Kalman 12 states, all products and the inverse (%d Newton-Schulz iterations) on the lane, 3 seeds: difference from the fp64 filter %s; RMSE vs truth: fp64 %.3f, lane %.3f; mean ||S^-1 S - I|| of the lane inverse %.2e" % (ITERS, ["%.2e" % r[0] for r in res], np.mean([r[1] for r in res]), np.mean([r[2] for r in res]), np.mean([r[3] for r in res])))
