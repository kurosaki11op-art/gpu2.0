"""28 Oct 2026, SIMULATED. Part 2b of fft_kalman_routing.py: error of an all-low-precision 12-state Kalman filter against the TRUTH (not against the fp64 filter). Re-uses the format helpers of fft_kalman_routing.py. An earlier inline version of this check had a covariance-update bug (a stray factor 0.5) and was discarded; this is the corrected one."""
import numpy as np
src = open(__file__.replace("kalman_truth_check.py", "fft_kalman_routing.py")).read().split("print(\"PART 1a")[0]
exec(src)
def mm(A, B, Q): return Q(Q(A) @ Q(B))
def kal(seed, Q, T=1000):
    r = np.random.RandomState(seed); n, m = 12, 6; Qr, _ = np.linalg.qr(r.randn(n, n)); F = 0.98 * Qr; H = r.randn(m, n) / np.sqrt(n); Qc = 0.01 * np.eye(n); R = 0.5 * np.eye(m)
    truth = r.randn(n); x = np.zeros(n); P = np.eye(n); rz = np.random.RandomState(seed + 100); err = []
    for t in range(T):
        truth = F @ truth + rz.randn(n) * 0.1; z = H @ truth + rz.randn(m) * np.sqrt(0.5)
        x = mm(F, x[:, None], Q)[:, 0]; P = mm(mm(F, P, Q), F.T, Q) + Qc; P = Q(0.5 * (P + P.T)); S = mm(mm(H, P, Q), H.T, Q) + R; K = mm(mm(P, H.T, Q), np.linalg.inv(S), Q)
        x = x + mm(K, (z - mm(H, x[:, None], Q)[:, 0])[:, None], Q)[:, 0]; P = mm(np.eye(n) - mm(K, H, Q), P, Q); P = Q(0.5 * (P + P.T)); err.append(np.linalg.norm(x - truth))
    return np.sqrt(np.mean(np.square(err[100:])))
print("PART 2b: RMSE of the state estimate against the truth, steps 100 to 1000, mean of 3 seeds")
for nm, Q in (("fp64", ID), ("fp32", fl(np.float32)), ("fp16", fl(np.float16)), ("bfloat16", bf16), ("int8", intq(8)), ("BFP8", bfp(8))):
    print("  %-9s %.3f" % (nm, np.mean([kal(s, Q) for s in range(3)])))
