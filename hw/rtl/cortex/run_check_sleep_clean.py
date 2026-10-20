#!/usr/bin/env python3
"""Sleep cleaning with the chip's own parts, bit-exact (20 Oct 2026): the ear's noisy names of NS buffered pictures are cleaned using (1) the class scores of the core (cortex_core.v, CORTEX_HOOKS build, rd_scores after one PREDICT per buffered picture), (2) the K nearest buffered pictures by shared code bits (cortex_neighbours.v),
and (3) the pooling (cortex_pool.v in RTL, and cross_modal.pool_names in software: adds and compares). The names obtained from the RTL's scores, neighbours AND pooling must equal the names obtained from the software model's. Scenario: 5 known classes (MNIST digits 0-4), the table learns 120 pictures under noisy names (25 % wrong), then NS = 32 buffered pictures are cleaned.
usage: python run_check_sleep_clean.py DATA_DIR [--margin=N]"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
from cortex_int import CortexInt, _count, _practise  # noqa
from cortex_core import load  # noqa
import detector_learn, cross_modal  # noqa
D = sys.argv[1]; MARGIN = int([a.split("=")[1] for a in sys.argv if a.startswith("--margin=")][0]) if any(a.startswith("--margin=") for a in sys.argv) else 256; NS, K, KC, SW, LW = 32, 8, 5, 5, 10; SAT = 1 << 19
xtr, ytr, xte, yte = load(D, "mnist"); ytr = ytr.astype(np.int64); r = np.random.RandomState(5)
fes = detector_learn.learn_features(xtr[np.isin(ytr, (0, 1))][:2000]); enc = lambda x: np.concatenate([g.encode(x) for g in fes], 1)
itr = np.concatenate([r.choice(np.where(ytr == c)[0], 24, replace=False) for c in range(KC)]); r.shuffle(itr); ibuf = np.concatenate([r.choice(np.where(ytr == c)[0], 8, replace=False) for c in range(KC)])[:NS]; r.shuffle(ibuf)
noisy = ytr[itr].copy(); flip = r.rand(len(itr)) < 0.25; noisy[flip] = (noisy[flip] + r.randint(1, KC, flip.sum())) % KC
ctr, cbuf = enc(xtr[itr]), enc(xtr[ibuf]); NB = ctr.shape[1]; ear = ytr[ibuf].copy(); f2 = r.rand(NS) < 0.30; ear[f2] = (ear[f2] + r.randint(1, KC, f2.sum())) % KC       # the ear's names of the buffered pictures (30 % wrong)
# model: the core learns the noisy names (the hooks scenario), then predicts every buffered picture
m = CortexInt(NB, B=10, ndream=10, night=0, daydream=0, margin=MARGIN); seeds = m.rng.copy(); cmds, scores_m = [], []
for c in range(KC): cmds.append((5, c, [])); m.known[c] = True
for i in range(len(itr)):
    a = np.array(np.nonzero(ctr[i])[0], np.int32); cmds.append((1, int(noisy[i]), a.tolist())); _count(m.on, m.n, a, len(a), int(noisy[i]), m.top); _practise(m.W, a, len(a), int(noisy[i]), m.known, m.margin, m.cmax)
for t in range(NS):
    a = np.array(np.nonzero(cbuf[t])[0], np.int64); cmds.append((4, 0, a.tolist())); scores_m.append([int(m.W[c, a].astype(np.int64).sum()) for c in range(10)])
words = []
for op, arg, lst in cmds: words += [op, arg, len(lst)] + list(lst)
words.append(0xFFFFFFFF)
open(os.path.join(HERE, "cmds.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n"); open(os.path.join(HERE, "lanes.hex"), "w").write("\n".join("%08x" % s for s in seeds) + "\n")
subprocess.run(["iverilog", "-g2005", "-DCORTEX_HOOKS", "-o", "/tmp/sc.vvp", f"-Ptb_cortex_core_hooks.NW={len(words) + 8}", f"-Ptb_cortex_core_hooks.NB={NB}", f"-Ptb_cortex_core_hooks.MARGIN={MARGIN}", "cortex_core.v", "tb_cortex_core_hooks.v"], cwd=HERE, check=True)
subprocess.run("vvp -n /tmp/sc.vvp | grep ^commands", shell=True, cwd=HERE, capture_output=True, text=True)
scores_r = [list(map(int, g.split()[1:])) for g in open(os.path.join(HERE, "out_cortex.txt")).read().split("\n") if g.startswith("S ")]
# neighbours: the buffered pictures' codes in the neighbour unit
lists = [np.nonzero(c)[0] for c in cbuf]; LWMAX = 1 << LW; words = []
for l in lists: words += [len(l)] + l.tolist() + [0] * (LWMAX - len(l))
open(os.path.join(HERE, "nb_codes.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n"); open(os.path.join(HERE, "nb_q.hex"), "w").write("\n".join("%08x" % q for q in range(NS)) + "\n")
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/nb.vvp", f"-Ptb_neighbours.NS={NS}", f"-Ptb_neighbours.SW={SW}", f"-Ptb_neighbours.K={K}", f"-Ptb_neighbours.NQ={NS}", "cortex_neighbours.v", "tb_neighbours.v"], cwd=HERE, check=True)
subprocess.run(["vvp", "-n", "/tmp/nb.vvp"], cwd=HERE, capture_output=True, text=True)
nb_r = np.array([[int(v) for v in l.split()][0::2] for l in open(os.path.join(HERE, "nb_out.txt")).read().split("\n") if l.strip()])
dense = cbuf.astype(np.int32); ov = dense @ dense.T; np.fill_diagonal(ov, -1); nb_m = np.argsort(-ov, 1, kind="stable")[:, :K]
known = np.zeros(10, bool); known[:KC] = True
names_r = cross_modal.pool_names(np.array(scores_r), nb_r, ear, known, ear_vote=200); names_m = cross_modal.pool_names(np.array(scores_m), nb_m, ear, known, ear_vote=200)
# the pooling in RTL (cortex_pool.v) on the RTL's own scores and neighbours
words = [int(sum(1 << c for c in range(10) if known[c])), NS]
for q in range(NS): words += [int(v) & 0xFFFFF for v in scores_r[q]] + [int(v) for v in nb_r[q]] + [int(ear[q])]
open(os.path.join(HERE, "pool_in.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/pool.vvp", f"-Ptb_pool.NS={NS}", f"-Ptb_pool.SW={SW}", f"-Ptb_pool.K={K}", "-Ptb_pool.EV=200", "cortex_pool.v", "tb_pool.v"], cwd=HERE, check=True)
subprocess.run(["vvp", "-n", "/tmp/pool.vvp"], cwd=HERE, capture_output=True, text=True)
names_p = np.array([int(l) for l in open(os.path.join(HERE, "pool_out.txt")).read().split("\n") if l.strip()])
bad = int((np.array(scores_r) != np.array(scores_m)).any(1).sum()) + int((nb_r != nb_m).any(1).sum()) + int((names_r != names_m).sum()) + int((names_p != names_m).sum())
print(f"buffered pictures {NS}, K {K}; score rows differing {int((np.array(scores_r) != np.array(scores_m)).any(1).sum())}, neighbour rows differing {int((nb_r != nb_m).any(1).sum())}, names differing {int((names_r != names_m).sum())}; names from the pooling unit differing {int((names_p != names_m).sum())}")
print(f"ear's names right {float((ear == ytr[ibuf]).mean()):.2f} -> cleaned names right {float((names_r == ytr[ibuf]).mean()):.2f} (true labels of the buffer used only to score)")
print("PASS" if bad == 0 else "FAIL")
