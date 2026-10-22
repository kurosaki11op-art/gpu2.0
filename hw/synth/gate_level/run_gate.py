import os, subprocess, sys
import numpy as np
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
from cortex_int import CortexInt, _count, _practise, _dream
NB = 64; CB = 10; r = np.random.RandomState(5); T = r.rand(3, NB) < 0.25
m = CortexInt(NB, B=CB, ndream=0, night=0, daydream=0); seeds = m.rng.copy(); cmds = []; exp = []; buf = np.zeros(NB, np.int32)
def ex(c): return np.nonzero(T[c] ^ (r.rand(NB) < 0.05))[0].astype(np.int32)
for c in range(3): cmds.append((5, c, [])); m.known[c] = True
for rep in range(3):
    for c in range(3):
        a = ex(c); cmds.append((1, c, a.tolist())); _count(m.on, m.n, a, len(a), c, m.top); exp.append("U %d" % _practise(m.W, a, len(a), c, m.known, m.margin, m.cmax))
        if rep >= 1:
            oc = (c + 1) % 3; k = _dream(m.on, m.n, oc, m.rng, buf); cmds.append((3, oc, [])); exp.append("D %d %d" % (k, _practise(m.W, buf, k, oc, m.known, m.margin, m.cmax)))
for c in range(3):
    for _ in range(2):
        a = ex(c); cmds.append((4, 0, a.tolist())); s = np.array([m.W[k, a].astype(np.int64).sum() if m.known[k] else -(1 << 40) for k in range(10)]); exp.append("P %d" % int(s.argmax()))
exp += ["N %d" % v for v in m.n]
for b in range(NB):
    w = sum((int(m.W[c, b]) & 0x1F) << (5 * c) for c in range(10)); cw = sum(int(m.on[c, b]) << (CB * c) for c in range(10)); exp.append("W %013x C %025x" % (w, cw))
words = []
for op, arg, lst in cmds: words += [op, arg, len(lst)] + list(lst)
words.append(0xFFFFFFFF)
open("cmds.hex", "w").write("\n".join("%08x" % w for w in words) + "\n"); open("lanes.hex", "w").write("\n".join("%08x" % s for s in seeds) + "\n")
def sim(name, files, top="tb_cortex_core"):
    subprocess.run(["iverilog", "-g2005", "-s", top, "-o", f"/tmp/gate/{name}.vvp", f"-P{top}.NB=64", f"-P{top}.AW=6", f"-P{top}.NW={len(words) + 8}"] + files, cwd="/tmp/gate", check=True)
    res = subprocess.run(f"vvp -n /tmp/gate/{name}.vvp | grep ^commands", shell=True, cwd="/tmp/gate", capture_output=True, text=True); print(name, res.stdout.strip())
    return [l for l in open("out_cortex.txt").read().split("\n") if l]
rtl = sim("rtl", ["cortex_core.v", "tb_cortex_core.v"])
cells = "cells_used.v"
gate = sim("gate", ["netlist_core.v", cells, "tb_gate.v"], "tb_cortex_core")
norm = lambda L: [x.upper() if x[0] in "WC" else x for x in L]
for name, got in (("RTL", rtl), ("gate-level netlist (Gowin primitives)", gate)):
    bad = sum(1 for a, e in zip(norm(got), norm(exp)) if a != e) + abs(len(got) - len(exp)); print(f"{name} vs integer model: {len(exp)} lines, mismatches {bad}")
print("gate vs RTL identical:", norm(gate) == norm(rtl))
