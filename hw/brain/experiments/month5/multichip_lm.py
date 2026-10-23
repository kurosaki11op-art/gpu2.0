"""Multi-chip test of the counting language model (23 Oct 2026) SIMULATED. The hashed count table (2^22 slots = 8 MB, as in counting_lm.py) is
split over N chips by slot number (chip = slot mod N, a hash-spread split). One token needs 48 lookups (6 context orders x 8 yes/no steps of
the byte). The 8 steps are sequential (the next step depends on the last bit), the 6 orders of one step are parallel. Measured on the real
text: the share of lookups that leave the home chip, the lookups per chip (load balance, skewed by frequent contexts), messages and bytes per token.
Then modelled with stated assumptions: latency and energy per token for the table lookups, and the same chip count for a dense 7-billion-parameter
model (analytic, 4-bit weights, pipeline split), for COST ONLY: the two models do not have the same quality.
usage: python multichip_lm.py"""
import math, sys, time
import numpy as np
from numba import njit
import pydoc_data.topics as T

text = "".join(T.topics.values()).encode("utf8", "ignore"); data = np.frombuffer(text, dtype=np.uint8).copy(); N = len(data)
NS = np.array([1, 2, 4, 8, 16, 32, 64], np.int64)


@njit(cache=True)
def sim(data, logM, maxorder, NS):
    M = 1 << logM
    h = np.zeros(maxorder + 1, np.uint64)
    load = np.zeros((len(NS), 64), np.int64)                 # lookups per chip
    remote = np.zeros(len(NS), np.int64); total = 0
    for t in range(len(data)):
        for j in range(maxorder + 1):
            x = np.uint64(1469598103934665603) + np.uint64(j) * np.uint64(0x9E3779B97F4A7C15)
            for i in range(j):
                b = data[t - 1 - i] if t - 1 - i >= 0 else 255
                x = (x ^ np.uint64(b)) * np.uint64(1099511628211)
            h[j] = x
        home = t % 1                                          # the token's controller chip is chip 0
        node = 1
        for bpos in range(7, -1, -1):
            for j in range(maxorder + 1):
                y = (h[j] + np.uint64(node) * np.uint64(0xBF58476D1CE4E5B9))
                y ^= y >> np.uint64(31); y *= np.uint64(0x94D049BB133111EB); y ^= y >> np.uint64(29)
                ii = np.int64(y & np.uint64(M - 1)); total += 1
                for k in range(len(NS)):
                    c = ii % NS[k]; load[k, c] += 1
                    if c != home: remote[k] += 1
            node = node * 2 + ((data[t] >> bpos) & 1)
    return load, remote, total


t0 = time.time(); load, remote, total = sim(data, 22, 5, NS)
toks = N; lk = total / toks
print("characters %d, lookups per token %.0f, %.0fs\n" % (toks, lk, time.time() - t0))
# --- assumptions (ESTIMATED, order of magnitude, stated so they can be challenged) ---
T_LINK = 200e-9      # chip-to-chip round trip of one lookup (direct-connect, compiler-scheduled links)
T_SRAM = 5e-9        # one on-chip lookup
E_SRAM = 14e-12      # J per macro access (SKY130 OpenRAM library figure, 13.8 pJ)
E_LINK = 5e-12       # J per bit moved between chips (on-board serial link, typical 1 to 10 pJ/bit)
B_REQ, B_RSP = 4, 2  # bytes per lookup: 4 request (address), 2 response (two 8-bit counters)
print("| chips | remote lookups | busiest chip / average | messages per token | bytes per token | latency per token (8 sequential steps) | energy per token (lookups + links) |")
print("|---|---|---|---|---|---|---|")
rows = []
for k, n in enumerate(NS):
    rem = remote[k] / total; imb = load[k, :n].max() / (load[k, :n].sum() / n); msgs = lk * rem; byt = msgs * (B_REQ + B_RSP)
    lat = 8 * (T_SRAM + (T_LINK if n > 1 else 0)); en = lk * E_SRAM + byt * 8 * E_LINK
    rows.append((n, rem, imb, msgs, byt, lat, en))
    print("| %d | %.1f %% | %.2f | %.1f | %.0f B | %.2f us | %.2f nJ |" % (n, 100 * rem, imb, msgs, byt, lat * 1e6, en * 1e9))
# dense 7B model, same number of chips, analytic: 4-bit weights, int8 activations, hidden 4096, 32 layers, pipeline split over the chips
P, HID, L, WB, E_MAC = 7e9, 4096, 32, 0.5, 0.2e-12
print("\nDense 7-billion-parameter model, 4-bit weights = %.1f GB, pipeline split, cost only (a different quality, see text):" % (P * WB / 1e9))
print("| SRAM per chip | chips needed | cross-chip bytes per token | compute energy per token (int8 MACs at 0.2 pJ, 45 nm figure) | link energy per token |")
print("|---|---|---|---|---|")
for mb, label in ((3, "3 MB (130 nm open macros, 400 mm2)"), (300, "300 MB (28 nm, 400 mm2, Groq-class 230 MB)"), (1200, "1.2 GB (7 nm, 400 mm2)")):
    chips = math.ceil(P * WB / (mb * 1e6)); byt = (chips - 1) * HID; print("| %s | %d | %d B | %.1f mJ | %.2f uJ |" % (label, chips, byt, P * 2 * E_MAC * 1e3, byt * 8 * E_LINK * 1e6))
print("\nCounting model table 8 MB needs: %.1f chips of 3 MB, 1 chip of 300 MB" % (8 / 3))
