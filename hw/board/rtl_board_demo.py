#!/usr/bin/env python3
"""The Tang Nano top-level design (cortex_board_top.v: UART + core + encoder) in RTL simulation (Icarus Verilog), learning and recognising digits (22 Oct 2026, SIMULATED RTL).
The host sends the UART protocol bytes of the real board (seed lanes, clear, KNOWN, LEARN with a code list, DREAM, PREDICT); the board design answers byte by byte. Teaches digits 0-3 in four stages (each new digit learned with dreams of the earlier ones), then asks it to
recognise held-out test images. The integer model gets the same bytes and must give the same replies (bit-exact); the accuracy reported is computed from the REPLY BYTES of the simulated board design. usage: python rtl_board_demo.py DATA_DIR"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "brain"))
from cortex_int import CortexInt, _count, _practise, _dream  # noqa
from cortex_core import load  # noqa
D = sys.argv[1]; NPER = int(os.environ.get("NPER", 20)); NTEST = int(os.environ.get("NTEST", 12)); DREAMS = int(os.environ.get("DREAMS", 2))
z = np.load(os.path.join(D, "sep_mnist_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, "mnist"); ytr, yte = ytr.astype(int), yte.astype(int); NB = ctr.shape[1]
m = CortexInt(NB); buf = np.zeros(NB, np.int32); cmds, replies, truth = [], [], []
def cmd(b, rep, label=None): cmds.append(bytes(b)); replies.append(bytes(rep)); truth.append(label)
cmd([0xE0], [0x5A]); cmd([0x53] + [x for s in m.rng.copy() for x in int(s).to_bytes(4, "little")], [0x53]); cmd([0x43], [0x43]); r = np.random.RandomState(7)
def lst(a): return [len(a) & 255, len(a) >> 8] + [x for v in a for x in (int(v) & 255, int(v) >> 8)]
for c in range(4):
    cmd([0x4B, c], [0x4B]); m.known[c] = True
    for idx in r.choice(np.where(ytr == c)[0], NPER, replace=False):
        a = np.nonzero(ctr[idx])[0].astype(np.int32)
        _count(m.on, m.n, a, len(a), c, m.top); u = _practise(m.W, a, len(a), c, m.known, m.margin, m.cmax); cmd([0x4C, c] + lst(a), [u])
        for oc in range(c):                                           # dreams of the earlier digits, so they are not overwritten
            for _ in range(DREAMS):
                k = _dream(m.on, m.n, oc, m.rng, buf); u = _practise(m.W, buf, k, oc, m.known, m.margin, m.cmax); cmd([0x44, oc], [k & 255, k >> 8, u])
tests = r.choice(np.where(yte < 4)[0], NTEST * 4, replace=False)
for t in tests:
    a = np.nonzero(cte[t])[0]; s = np.array([m.W[c, a].astype(int).sum() if m.known[c] else -(1 << 40) for c in range(10)]); cmd([0x50] + lst(a), [int(s.argmax())], int(yte[t]))
allb = b"".join(cmds)
open(os.path.join(HERE, "in_cortex.hex"), "w").write("\n".join("%02x" % x for x in allb) + "\n")
open(os.path.join(HERE, "in_cortex_n.hex"), "w").write("\n".join("%04x\n%04x" % (len(c), len(rp)) for c, rp in zip(cmds, replies)) + "\n")
print(f"{len(cmds)} commands, {len(allb)} bytes to the board design", flush=True)
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/boarddemo.vvp", f"-Ptb_cortex_board.NBYTES={len(allb) + 4}", "-I", "../rtl/cortex", "cortex_board_top.v", "uart_rx.v", "uart_tx.v", "../rtl/cortex/cortex_core.v", "../rtl/cortex/cortex_encoder.v", "tb_cortex_board.v"], cwd=HERE, check=True)
res = subprocess.run(["vvp", "-n", "/tmp/boarddemo.vvp"], cwd=HERE, capture_output=True, text=True); print(res.stdout.strip().splitlines()[-1] if res.stdout.strip() else res.stderr[-300:])
got = bytes(int(x, 16) for x in open(os.path.join(HERE, "out_cortex_board.txt")).read().split()); exp = b"".join(replies)
bad = sum(a != b for a, b in zip(got, exp)) + abs(len(got) - len(exp))
# the replies of the PREDICT commands, in order, are the board design's answers
pos = 0; ans = []
for c, rp, tr in zip(cmds, replies, truth):
    if tr is not None: ans.append((got[pos], tr))
    pos += len(rp)
right = sum(1 for a, t in ans if a == t)
print(f"reply bytes expected {len(exp)} got {len(got)}, mismatches against the integer model {bad}")
print(f"the simulated board design recognised {right} of {len(ans)} held-out test digits ({100 * right / len(ans):.1f} %) after learning digits 0-3 from {NPER} examples each")
print("PASS" if bad == 0 else "FAIL")
