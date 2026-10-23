"""Multiplier-free hash variant of the counting language model test (23 Oct 2026): the hash uses only shifts, rotates and XOR; compares bits per character with the multiplying hash. Original docstring follows. Counting language model test (23 Oct 2026) SIMULATED, algorithm test only (not yet mapped to the chip).
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

text = "".join(T.topics.values()).encode("utf8", "ignore")
data = np.frombuffer(text, dtype=np.uint8).copy()
if os.environ.get("QUICK"): data = data[:120000]
N = len(data)


@njit(cache=False)
def run_mf(data, logM, maxorder, k, a, upto):
    M = 1 << logM
    n0 = np.zeros(M, np.uint8); n1 = np.zeros(M, np.uint8)
    h = np.zeros(maxorder + 1, np.uint64)
    idx = np.zeros(maxorder + 1, np.int64)
    bits = 0.0; bits_tail = 0.0; tail_from = upto // 2
    for t in range(upto):
        c = data[t]
        for j in range(maxorder + 1):                     # context hash of the last j bytes
            x = np.uint64(0x9E3779B97F4A7C15) ^ (np.uint64(j) << np.uint64(33)) ^ (np.uint64(j) << np.uint64(7))
            for i in range(j):
                b = data[t - 1 - i] if t - 1 - i >= 0 else 255
                x = x ^ np.uint64(b); x = (x << np.uint64(5)) | (x >> np.uint64(59)); x ^= x << np.uint64(13); x ^= x >> np.uint64(7); x ^= x << np.uint64(17)
            h[j] = x
        node = 1
        for bpos in range(7, -1, -1):
            s = 0.0
            for j in range(maxorder + 1):
                y = h[j] ^ (np.uint64(node) << np.uint64(20)) ^ (np.uint64(node) << np.uint64(47))
                y ^= y << np.uint64(13); y ^= y >> np.uint64(7); y ^= y << np.uint64(17); y ^= y >> np.uint64(31)
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



@njit(cache=False)
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
print("| table slots | multiplier-free hash (all / second half) | multiplying hash (all / second half) |"); print("|---|---|---|")
for logM in (16, 20, 22, 24):
    b, bt = run_mf(data, logM, 5, 0.25, 0.2, N); b0, bt0 = run(data, logM, 5, 0.25, 0.2, N)
    print("| 2^%d | %.3f / %.3f | %.3f / %.3f |" % (logM, b, bt, b0, bt0), flush=True)
