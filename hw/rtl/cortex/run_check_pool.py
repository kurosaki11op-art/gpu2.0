#!/usr/bin/env python3
"""cortex_pool.v vs cross_modal.pool_names (20 Oct 2026), bit-exact: the new names of buffered pictures from class scores, neighbour slots and the ear's names. Cases: (1) random scores and neighbours with 10, 6 and 1 known classes (ties and negative scores included, 32 slots, K = 8); (2) the real sleep-cleaning data of run_check_sleep_clean.py (scores of the core, neighbours of the neighbour unit) when DATA_DIR has MNIST.
usage: python run_check_pool.py [DATA_DIR]"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
import cross_modal  # noqa
NS, K, C, EV = 32, 8, 10, 200
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/pool.vvp", f"-Ptb_pool.NS={NS}", f"-Ptb_pool.K={K}", f"-Ptb_pool.EV={EV}", "cortex_pool.v", "tb_pool.v"], cwd=HERE, check=True)
bad = 0; cases = []
r = np.random.RandomState(11)
for nk in (10, 6, 1, 10):
    known = np.zeros(C, bool); known[r.choice(C, nk, replace=False)] = True; scores = r.randint(-3000, 3000, (NS, C)); scores[r.rand(NS, C) < 0.2] = 0; scores[:4, :] = 5            # ties
    nb = np.stack([r.choice([j for j in range(NS) if j != q], K, replace=False) for q in range(NS)]); names = r.choice(np.where(known)[0], NS); cases.append((known, scores, nb, names))
for known, scores, nb, names in cases:
    words = [int(sum(1 << c for c in range(C) if known[c])), NS]
    for q in range(NS): words += [int(v) & 0xFFFFF for v in scores[q]] + [int(v) for v in nb[q]] + [int(names[q])]
    open(os.path.join(HERE, "pool_in.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
    res = subprocess.run("vvp -n /tmp/pool.vvp | grep ^slots", shell=True, cwd=HERE, capture_output=True, text=True)
    got = np.array([int(l) for l in open(os.path.join(HERE, "pool_out.txt")).read().split("\n") if l.strip()]); exp = cross_modal.pool_names(scores, nb, names, known, ear_vote=EV)
    d = int((got != exp).sum()); bad += d; print(f"known {int(known.sum()):2d}: {res.stdout.strip()}; names differing {d}")
print("PASS" if bad == 0 else "FAIL")
