"""Memory priming: every recall order that hits adds a boost to its byte's logit (votes add up)."""
import sys, numpy as np, itertools
from recall_lib import recall
F = np.load(sys.argv[1]); split = sys.argv[2]
seq, LM = F[split + '_seq'].astype(np.int64), F[split + '_lm'].astype(np.int64)
N = len(seq) - 1; y = seq[1:]; LM = LM[:N]
def all_orders(orders, bits):
    """recall each order separately (its own table share) -> per-order (pred, conf)"""
    return [recall(seq, (k,), bits) for k in orders]
oracle_sets = {}
for orders, bits in [((3,), 10), ((2, 3, 5), 10), ((2, 3, 4, 6), 10), ((1, 2, 3, 4, 6), 10)]:
    R = all_orders(orders, bits)
    best = (0, None)
    grid = [0, 64, 128, 256, 512] 
    for base_b in grid[1:]:
        for slope in (0, 32, 64, 128):
            for ow in itertools.product((0.5, 1, 2), repeat=1):
                lg = LM.copy().astype(np.int64)
                for i, (p, c, o) in enumerate(R):
                    k = orders[i]; hit = p >= 0
                    w = (base_b + slope * c) * (k / 3.0) ** (ow[0] - 1 if ow[0] != 1 else 0)
                    lg[np.where(hit)[0], p[hit]] += w[hit].astype(np.int64) if np.ndim(w) else int(w)
                acc = np.mean(lg.argmax(1) == y)
                if acc > best[0]: best = (acc, (base_b, slope, ow))
    print(f'orders {orders}, {1 << bits} slots per order: priming best {best[0]:.1%} params {best[1]}', flush=True)
