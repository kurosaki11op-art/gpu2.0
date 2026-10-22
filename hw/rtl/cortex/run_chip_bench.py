#!/usr/bin/env python3
"""Cycle counts of the virtual chip (22 Oct 2026, SIMULATED RTL): how many clock cycles cortex_core.v needs per LEARN, DREAM and PREDICT at the real size (4,608 code bits, about 263 active), measured in RTL simulation (Icarus Verilog) on real digit codes,
for the FPGA build and the pipelined build (an ASIC option). Converted to latency and throughput at a clock you choose (board clock 27 MHz, the place-and-route estimate allows about 54 MHz). The cycle counts are exact for the design; the times are MODELLED from them.
usage: python run_chip_bench.py DATA_DIR [--n 3] [--mhz 27]"""
import argparse, os, subprocess, sys, tempfile
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
from cortex_int import CortexInt  # noqa
from cortex_core import load  # noqa
VVP = os.path.join(tempfile.gettempdir(), "bench.vvp")
ap = argparse.ArgumentParser(); ap.add_argument("data"); ap.add_argument("--n", type=int, default=3); ap.add_argument("--mhz", type=float, default=27.0); a = ap.parse_args()
z = np.load(os.path.join(a.data, "sep_mnist_F32_p2.npz")); ctr, cte = z["tr"], z["te"]; _, ytr, _, yte = load(a.data, "mnist"); ytr = ytr.astype(int); NB = ctr.shape[1]
r = np.random.RandomState(1); m = CortexInt(NB); seeds = m.rng.copy(); cmds = []
for c in (0, 1): cmds.append((5, c, []))
for c in (0, 1):
    for i in r.choice(np.where(ytr == c)[0], a.n + 2, replace=False): cmds.append((1, c, np.nonzero(ctr[i])[0].tolist()))
for _ in range(a.n): cmds.append((3, 0, [])); cmds.append((3, 1, []))
for i in r.choice(len(cte), a.n, replace=False): cmds.append((4, 0, np.nonzero(cte[i])[0].tolist()))
words = []
for op, arg, lst in cmds: words += [op, arg, len(lst)] + list(lst)
words.append(0xFFFFFFFF); open(os.path.join(HERE, "cmds.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n"); open(os.path.join(HERE, "lanes.hex"), "w").write("\n".join("%08x" % s for s in seeds) + "\n")
print(f"{'build':<22} {'LEARN':>10} {'DREAM':>10} {'PREDICT':>10}   (clock cycles, mean over the measured commands)")
for build, flags in (("FPGA build", []), ("pipelined (ASIC option)", ["-DCORTEX_PIPE"])):
    subprocess.run(["iverilog", "-g2005", "-s", "tb_bench", "-o", VVP, f"-Ptb_bench.NW={len(words) + 8}", "cortex_core.v", "tb_bench.v"] + flags, cwd=HERE, check=True)
    subprocess.run(["vvp", "-n", VVP], cwd=HERE, stdout=subprocess.DEVNULL)
    rows = [l.split() for l in open(os.path.join(HERE, "out_bench.txt")).read().split("\n") if l.startswith("C")]
    cyc = {op: np.mean([int(x[3]) for x in rows if int(x[1]) == op]) for op in (1, 3, 4)}
    print(f"{build:<22} {cyc[1]:>10.0f} {cyc[3]:>10.0f} {cyc[4]:>10.0f}")
    t = {op: cyc[op] / (a.mhz * 1e6) for op in cyc}
    print(f"{'  at %.0f MHz' % a.mhz:<22} {t[1] * 1e3:>8.2f}ms {t[3] * 1e3:>8.2f}ms {t[4] * 1e3:>8.3f}ms   -> a decision every {t[4] * 1e3:.3f} ms = {1 / t[4]:.0f} decisions/s (one chip, one stream)")
