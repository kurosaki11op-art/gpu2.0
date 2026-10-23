"""Hot-row copies for the multi-chip counting language model (23 Oct 2026) SIMULATED. The most used table slots (chosen on the first half of the text)
are copied to every chip; lookups to them become local. Evaluated on the second half. Reports, for 16 and 64 chips, the share of lookups that leave the
home chip and the load on the busiest chip against the average, for K copied slots (each copy costs one slot of memory on every chip).
usage: python hot_rows.py"""
import numpy as np
from numba import njit
import pydoc_data.topics as T
text = "".join(T.topics.values()).encode("utf8", "ignore"); data = np.frombuffer(text, dtype=np.uint8).copy(); N = len(data)


@njit(cache=True)
def slots(data, lo, hi, logM, maxorder):
    M = 1 << logM; out = np.zeros((hi - lo) * 48, np.int64); h = np.zeros(maxorder + 1, np.uint64); q = 0
    for t in range(lo, hi):
        for j in range(maxorder + 1):
            x = np.uint64(1469598103934665603) + np.uint64(j) * np.uint64(0x9E3779B97F4A7C15)
            for i in range(j):
                b = data[t - 1 - i] if t - 1 - i >= 0 else 255
                x = (x ^ np.uint64(b)) * np.uint64(1099511628211)
            h[j] = x
        node = 1
        for bpos in range(7, -1, -1):
            for j in range(maxorder + 1):
                y = (h[j] + np.uint64(node) * np.uint64(0xBF58476D1CE4E5B9)); y ^= y >> np.uint64(31); y *= np.uint64(0x94D049BB133111EB); y ^= y >> np.uint64(29)
                out[q] = np.int64(y & np.uint64(M - 1)); q += 1
            node = node * 2 + ((data[t] >> bpos) & 1)
    return out


A = slots(data, 0, N // 2, 22, 5); B = slots(data, N // 2, N, 22, 5)
cnt = np.bincount(A, minlength=1 << 22); order = np.argsort(-cnt)
print("lookups per half %d, distinct slots used in the second half %d" % (len(B), len(np.unique(B))))
print("| chips | copied slots K | memory cost (slots on every chip, of 4.2 M) | remote lookups | busiest chip / average |")
print("|---|---|---|---|---|")
for n in (16, 64):
    for K in (0, 64, 256, 1024, 4096, 16384):
        hot = np.zeros(1 << 22, bool); hot[order[:K]] = True
        isHot = hot[B]; rem = float((~isHot).mean() * (n - 1) / n)           # a cold lookup is remote with probability (n-1)/n; a hot lookup is local on any chip
        # load: cold lookups go to their owner chip (slot mod n); hot lookups are served by the requesting chip itself (spread evenly)
        load = np.bincount((B[~isHot] % n), minlength=n).astype(float) + isHot.sum() / n
        print("| %d | %d | %.2f %% | %.1f %% | %.2f |" % (n, K, 100 * K / (1 << 22), 100 * rem, load.max() / load.mean()))
