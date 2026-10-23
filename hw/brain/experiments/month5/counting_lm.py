"""Counting language model test (23 Oct 2026) SIMULATED, algorithm test only (not yet mapped to the chip).
Question: does a language model built ONLY from hashed count tables (no matrix, no multiplier in the table path, no backprop,
learning on the fly, each character seen once) reach useful quality, and does quality grow with table memory?
Text: Python's own documentation (pydoc topics, about 560 KB of English technical text), read from the standard library.
Protocol: prequential (predict each character, then learn it), so every number is a one-pass online result.
The next byte is predicted as 8 binary decisions (a binary tree over the 255 prefixes). Each decision looks up one pair of counters
(n0, n1, 8-bit, halved at 255) per context order, in a hashed table of M slots (shared by all nodes and orders, no collision check).
The decision score is the sum of the per-order log-odds ln((n1+a)/(n0+a)); p = 1/(1+exp(-k*s)); k is one global scale.
usage: python counting_lm.py  -> prints a table; env QUICK=1 for a short run."""
import math, os, sys, time, bz2, lzma, zlib
import numpy as np
from numba import njit
import pydoc_data.topics as T

text = open(os.environ["TEXTFILE"], "rb").read() if os.environ.get("TEXTFILE") else "".join(T.topics.values()).encode("utf8", "ignore")
data = np.frombuffer(text, dtype=np.uint8).copy()
if os.environ.get("QUICK"): data = data[:120000]
N = len(data)


@njit(cache=True)
def run(data, logM, maxorder, k, a, upto):
    M = 1 << logM
    n0 = np.zeros(M, np.uint8); n1 = np.zeros(M, np.uint8)
    h = np.zeros(maxorder + 1, np.uint64)
    idx = np.zeros(maxorder + 1, np.int64)
    bits = 0.0; bits_tail = 0.0; tail_from = upto // 2
    for t in range(upto):
        c = data[t]
        for j in range(maxorder + 1):                     # context hash of the last j bytes
            x = np.uint64(1469598103934665603) + np.uint64(j) * np.uint64(0x9E3779B97F4A7C15)
            for i in range(j):
                b = data[t - 1 - i] if t - 1 - i >= 0 else 255
                x = (x ^ np.uint64(b)) * np.uint64(1099511628211)
            h[j] = x
        node = 1
        for bpos in range(7, -1, -1):
            s = 0.0
            for j in range(maxorder + 1):
                y = (h[j] + np.uint64(node) * np.uint64(0xBF58476D1CE4E5B9))
                y ^= y >> np.uint64(31); y *= np.uint64(0x94D049BB133111EB); y ^= y >> np.uint64(29)
                ii = np.int64(y & np.uint64(M - 1)); idx[j] = ii
                s += math.log((n1[ii] + a) / (n0[ii] + a))
            bit = (c >> bpos) & 1
            z = k * s
            if z > 30.0: z = 30.0
            if z < -30.0: z = -30.0
            p1 = 1.0 / (1.0 + math.exp(-z))
            pp = p1 if bit == 1 else 1.0 - p1
            if pp < 1e-6: pp = 1e-6
            cost = -math.log(pp) / math.log(2.0)
            bits += cost
            if t >= tail_from: bits_tail += cost
            for j in range(maxorder + 1):
                ii = idx[j]
                if bit == 1:
                    n1[ii] += 1
                    if n1[ii] == 255: n1[ii] >>= 1; n0[ii] >>= 1
                else:
                    n0[ii] += 1
                    if n0[ii] == 255: n0[ii] >>= 1; n1[ii] >>= 1
            node = node * 2 + bit
    return bits / upto, bits_tail / (upto - tail_from)


t0 = time.time()
res = {}
print("characters:", N, "| reference compressors on the whole text (bits per character, not online):",
      "zlib-9 %.3f" % (8 * len(zlib.compress(text, 9)) / N), "bz2 %.3f" % (8 * len(bz2.compress(text, 9)) / N), "xz %.3f" % (8 * len(lzma.compress(text, preset=9)) / N), flush=True)
cnt = np.bincount(data, minlength=256).astype(float) / N
print("unigram entropy %.3f bits per character" % -(cnt[cnt > 0] * np.log2(cnt[cnt > 0])).sum(), flush=True)

# 1. scale k and pseudo-count a (picked once on order 5, 2^22 slots)
best = None
for k in (0.25, 0.4, 0.6, 0.8, 1.0):
    for a in (0.2, 0.4):
        b, bt = run(data, 22, 5, k, a, N)
        if best is None or b < best[0]: best = (b, k, a)
print("best k=%.2f a=%.2f (bits per char %.3f), %.0fs" % (best[1], best[2], best[0], time.time() - t0), flush=True)
_, K, A = best
rows = []
print("\n| context orders 0..n | table slots | memory (8+8 bit counters) | bits per char (all) | bits per char (second half) |", flush=True)
print("|---|---|---|---|---|", flush=True)
for order in (1, 2, 3, 4, 5, 6):
    b, bt = run(data, 24, order, K, A, N); rows.append((order, 24, b, bt))
    print("| 0..%d | 2^24 | 32 MB | %.3f | %.3f |" % (order, b, bt), flush=True)
for logM in (12, 14, 16, 18, 20, 22, 24):
    b, bt = run(data, logM, 5, K, A, N); rows.append((5, logM, b, bt))
    print("| 0..5 | 2^%d | %s | %.3f | %.3f |" % (logM, ("%.0f KB" % ((1 << logM) * 2 / 1024)) if logM < 19 else ("%.1f MB" % ((1 << logM) * 2 / 2 ** 20)), b, bt), flush=True)
print("done %.0fs" % (time.time() - t0))
