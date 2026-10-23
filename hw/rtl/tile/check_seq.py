#!/usr/bin/env python3
"""Compares the hardware token sequencer (tb_seq.v, seq_out.txt) with a Python model that uses the same multiplier-free hash, the same table contents and
the same fixed-point log-odds ROM: every step's sum s and bit must be identical. usage: python check_seq.py NTOK"""
import math, sys
NT = int(sys.argv[1]) if len(sys.argv) > 1 else 60
M = (1 << 64) - 1
text = [int(l, 16) for l in open("text.hex").read().split()]
L = [int(round(256 * math.log(x + 0.2))) for x in range(256)]
def xs(x): x ^= (x << 13) & M; x ^= x >> 7; x ^= (x << 17) & M; return x
def ctxhash(j, hist):
    x = (0x9E3779B97F4A7C15 ^ (j << 33) ^ (j << 7)) & M
    for i in range(j): x ^= hist[i]; x = ((x << 5) | (x >> 59)) & M; x = xs(x)
    return x
def slot(h, node): y = (h ^ (node << 20) ^ (node << 47)) & M; y = xs(y); y ^= y >> 31; return y & ((1 << 22) - 1)
exp = []
for t in range(NT):
    hist = [text[t - i - 1] if t - i - 1 >= 0 else 255 for i in range(5)]; hs = [ctxhash(j, hist) for j in range(6)]; node = 1
    for step in range(7, -1, -1):
        s = 0
        for j in range(6):
            addr = slot(hs[j], node) >> 4; f = (addr * 40503 + (addr >> 3)) & 0xFFFF; s += L[(f >> 8) & 255] - L[f & 255]
        s = ((s + 32768) & 0xFFFF) - 32768; bit = (text[t] >> step) & 1; exp.append((s, bit)); node = node * 2 + bit
got = [tuple(map(int, l.split())) for l in open("seq_out.txt")]
bad = sum(1 for a, b in zip(got, exp) if a != b) + abs(len(got) - len(exp))
print("steps checked %d, hardware %d, mismatches %d" % (len(exp), len(got), bad)); print("PASS" if bad == 0 else "FAIL")
