"""Integer grouping, division-free rate prototypes (22 Oct 2026) SIMULATED. prototype rate levels R = round(4 c / m) in 0..4 found by compares only: R = #{l in 1..4 : 8 c >= (2 l - 1) m}; score = sum over active bits of R - (sum R^2) >> 3. Init: pairs at stride N / K from an offset per restart. usage: CODES.npz"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
z = np.load(sys.argv[1]); X = z["joint"].astype(bool); y = z["y"]; K = 10; N = len(X); Xi = X.astype(np.int32)
def purity(a): return float(sum(np.bincount(y[a == j], minlength=10).max() for j in range(K) if (a == j).any()) / len(y))
SQ = np.array([0, 1, 4, 9, 16])
def level(c, m): return sum((8 * c >= (2 * l - 1) * m).astype(np.int32) for l in range(1, 5))
def km(iters, restarts, offs):
    best = (None, None)
    for r in range(restarts):
        idx = [((i * N) // K + (r * N) // (K * restarts)) % N for i in range(K)] if offs else list(range(r, r + K))
        R = X[idx].astype(np.int32) * 4
        for _ in range(iters):
            sc = Xi @ R.T - (SQ[R].sum(1)[None, :] >> 3); a = sc.argmax(1)
            for j in range(K):
                m = int((a == j).sum())
                if m: R[j] = level(Xi[a == j].sum(0), m)
        sc = Xi @ R.T - (SQ[R].sum(1)[None, :] >> 3); tot = int(sc.max(1).sum())
        if best[0] is None or tot > best[0]: best = (tot, sc.argmax(1))
    return best[1]
for iters in (8, 16):
    for restarts in (1, 3, 6):
        print("levels 0..4, stride init, %2d iterations, %d restarts: purity %.3f" % (iters, restarts, purity(km(iters, restarts, True))), flush=True)
