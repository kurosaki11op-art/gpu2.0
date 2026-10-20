#!/usr/bin/env python3
"""cortex_neighbours.v vs the Python overlap / argsort used in cross_modal.clean_names (20 Oct 2026), bit-exact, on real two-sense-sized codes: slots hold MNIST picture codes (4,608 bits, about 240 active) joined with FSDD sound codes (4,608 bits, about 380 active) when DATA has them, else picture codes only. Some slots are left empty. For every query slot the K neighbours (slot, overlap), best first, ties to the lower slot, must equal the model.
usage: python run_check_neighbours.py DATA_DIR [NS=16] [K=4]"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
import detector_learn  # noqa
from cortex_core import load  # noqa
D = sys.argv[1]; NS = int(sys.argv[2]) if len(sys.argv) > 2 else 16; K = int(sys.argv[3]) if len(sys.argv) > 3 else 4; LW = 10; LWMAX = 1 << LW; SW = int(np.ceil(np.log2(NS)))
xtr, ytr, xte, yte = load(D, "mnist"); r = np.random.RandomState(2); fes = detector_learn.learn_features(xtr[np.isin(ytr.astype(int), (0, 1))][:2000])
sel = r.choice(len(xtr), NS, replace=False); codes = np.concatenate([f.encode(xtr[sel]) for f in fes], 1); NBTOT = codes.shape[1]
lists = [np.nonzero(c)[0] for c in codes]
empty = set(r.choice(NS, max(1, NS // 8), replace=False).tolist()); lists = [np.zeros(0, int) if i in empty else l for i, l in enumerate(lists)]
words = []
for l in lists: words += [len(l)] + l.tolist() + [0] * (LWMAX - len(l))
open(os.path.join(HERE, "nb_codes.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
queries = [q for q in range(NS) if q not in empty][:min(NS, 6)]; open(os.path.join(HERE, "nb_q.hex"), "w").write("\n".join("%08x" % q for q in queries) + "\n")
dense = np.zeros((NS, NBTOT), np.int32)
for i, l in enumerate(lists): dense[i, l] = 1
ov = dense @ dense.T; exp = []
for q in queries:
    cand = [t for t in range(NS) if t != q and len(lists[t]) > 0]; order = sorted(cand, key=lambda t: (-int(ov[q, t]), t))[:K]            # best overlap first, ties to the lower slot
    exp.append(" ".join(f"{t} {int(ov[q, t])}" for t in order) + (" 0 0" * (K - len(order))))
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/nb.vvp", f"-Ptb_neighbours.NS={NS}", f"-Ptb_neighbours.SW={SW}", f"-Ptb_neighbours.K={K}", f"-Ptb_neighbours.NQ={len(queries)}", "cortex_neighbours.v", "tb_neighbours.v"], cwd=HERE, check=True)
res = subprocess.run(["vvp", "-n", "/tmp/nb.vvp"], cwd=HERE, capture_output=True, text=True); print(res.stdout.strip().splitlines()[-2] if len(res.stdout.strip().splitlines()) > 1 else res.stdout.strip())
got = [" ".join(l.split()) for l in open(os.path.join(HERE, "nb_out.txt")).read().split("\n") if l.strip()]
bad = sum(1 for a, e in zip(got, exp) if a != e) + abs(len(got) - len(exp))
for a, e in [(a, e) for a, e in zip(got, exp) if a != e][:4]: print("  MISMATCH rtl:", a, " model:", e)
print(f"slots {NS} (empty {sorted(empty)}), K {K}, queries {len(queries)}, active bits per code {np.mean([len(l) for l in lists if len(l)]):.0f}, overlaps of the top neighbour {[int(ov[q, int(g.split()[0])]) for q, g in zip(queries, got)]}")
print("lines compared", len(exp), "mismatches", bad); print("PASS" if bad == 0 else "FAIL")
