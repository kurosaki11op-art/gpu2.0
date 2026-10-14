#!/usr/bin/env python3
"""Simulate lookup_board_top end to end (iverilog) and check every byte the board sends against the reference model.
usage (from hw/board): python check_lookup_board.py"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "system"))
from lookup_ref import LookupCoreV2  # noqa
N1, N2, TB = 40, 200, 10
Z = np.load(os.path.join(HERE, "..", "system", "out", "slice_cache.npz")); data = bytes(Z["test_text"][:N1 + N2 + 1])
open(os.path.join(HERE, "in_board.hex"), "w").write("\n".join("%02x" % b for b in data) + "\n")
src = ["../rtl/lookup/spark_lookup2.v", "uart_rx.v", "uart_tx.v", "lookup_board_top.v", "tb_lookup_board.v"]
subprocess.run(["iverilog", "-g2012", "-o", "/tmp/lkb.vvp"] + src, cwd=HERE, check=True)
out = subprocess.run(["vvp", "-n", "/tmp/lkb.vvp"], cwd=HERE, capture_output=True, text=True).stdout
print(out.strip().splitlines()[-1])
got = [int(x, 16) for x in open(os.path.join(HERE, "rx_lookup.txt")).read().split()]

lut = [int(x, 16) for x in open(os.path.join(HERE, "..", "rtl", "lookup", "conf_lut.hex")).read().split()]
st = {}


def reset():
    st.update(core=LookupCoreV2(TB), n=0, c=0, h=0, last=None)


def feed(b):
    if st["last"] is not None and st["last"] == b: st["c"] += 1
    r = st["core"].step(b); st["n"] += 1; st["h"] += r[1]; st["last"] = r[0]
    return r


def d1(b):
    p, h, s, c, bk = feed(b); flags = (c << 4) | (s << 1) | h; cf = lut[bk]
    return [p, flags, cf, p ^ flags ^ cf]


def f0():
    bs = b"".join(int(v).to_bytes(4, "little") for v in (st["n"], st["c"], st["h"])); x = 0
    for v in bs: x ^= v
    return list(bs) + [x]


reset(); exp = [0x5A]
for i in range(N1): exp += d1(data[i])
preds = [feed(data[N1 + i])[0] for i in range(N2)]; x = 0
for v in preds: x ^= v
exp += preds + [x]
exp += f0()
exp += [0xC3]; lut[20] = 0x77
exp += d1(data[N1 + N2])
exp += [0xB1]; reset()
for i in range(10): exp += d1(data[i])
exp += f0() + [0xA1, 0xA0]
bad = [i for i, (a, b) in enumerate(zip(got, exp)) if a != b]
print(f"board replies: {len(got)} bytes received, {len(exp)} expected, mismatches {len(bad) + abs(len(got) - len(exp))}")
if bad: print("first mismatches at", bad[:5], [(got[i], exp[i]) for i in bad[:5]])
print("PASS" if not bad and len(got) == len(exp) else "FAIL")
sys.exit(0 if not bad and len(got) == len(exp) else 1)
