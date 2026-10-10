"""Learned arbiter (metacognition learned on-chip): which source to trust, per situation bucket.
bucket = (recall confidence 0..3, recall order idx, network margin bucket). Saturating counter per bucket:
 +1 when only recall was right, -1 when only the network was right. Use recall if counter >= 0."""
import sys, numpy as np
from recall_lib import recall
F = np.load(sys.argv[1]); split = sys.argv[2]
seq, LM = F[split + '_seq'].astype(np.int64), F[split + '_lm'].astype(np.int64)
N = len(seq) - 1; y = seq[1:]
srt = np.sort(LM, 1); margin = (srt[:, -1] - srt[:, -2])[:N]; netp = LM.argmax(1)[:N]
def mb(m):  # log2 margin bucket 0..7
    return np.minimum(np.floor(np.log2(np.maximum(m, 1))).astype(int), 7)
print(f'network alone {np.mean(netp == y):.1%}')
for orders, bits in [((3,), 10), ((3,), 11), ((3, 5), 11), ((3, 4, 6), 11), ((2, 3, 5), 11), ((2, 3, 4, 6), 11)]:
    p, c, o = recall(seq, orders, bits)
    hit = p >= 0
    fixed = max(np.mean(np.where(hit & (margin < th), p, netp) == y) for th in (16, 32, 64, 128))
    oi = np.array([orders.index(k) if k in orders else 0 for k in o])
    for cmax in (3, 7, 15):
        cnt = np.zeros((4, len(orders), 8), int); out = np.empty(N, int)
        for t in range(N):
            if not hit[t]: out[t] = netp[t]; continue
            b = (c[t], oi[t], mb(margin[t]))
            out[t] = p[t] if cnt[b] >= 0 else netp[t]
            rr, nr = p[t] == y[t], netp[t] == y[t]
            if rr and not nr: cnt[b] = min(cnt[b] + 1, cmax)
            elif nr and not rr: cnt[b] = max(cnt[b] - 1, -cmax - 1)
        print(f'orders {orders} {1 << bits} slots: fixed-threshold best {fixed:.1%} | learned arbiter (counter ±{cmax}) {np.mean(out == y):.1%} '
              f'last half {np.mean(out[N//2:] == y[N//2:]):.1%}', flush=True)
