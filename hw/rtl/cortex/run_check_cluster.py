#!/usr/bin/env python3
"""cortex_cluster.v vs cross_modal.kmeans_int (22 Oct 2026), bit-exact: the grouping of a buffer of unlabelled pairs (rate prototypes, compares and adds only). Random buffers of noisy copies of a few templates, several seeds and shapes; compared: the winning restart's total score and the group of every pair.
usage: python run_check_cluster.py"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
import cross_modal  # noqa
NB, NS, LM = 256, 48, 40; bad = 0
for K, ITER, RST, seed in ((4, 3, 2, 1), (4, 3, 2, 2), (3, 4, 3, 3), (5, 2, 2, 4), (4, 3, 1, 5)):
    subprocess.run(["iverilog", "-g2005", "-o", "/tmp/cl.vvp", f"-Ptb_cluster.K={K}", f"-Ptb_cluster.ITER={ITER}", f"-Ptb_cluster.RST={RST}", "cortex_cluster.v", "tb_cluster.v"], cwd=HERE, check=True)
    r = np.random.RandomState(seed); T = r.rand(K, NB) < 0.10; X = np.zeros((NS, NB), bool)
    for i in range(NS):
        X[i] = T[r.randint(K)] ^ (r.rand(NB) < 0.03)
        if X[i].sum() > LM: X[i, np.where(X[i])[0][LM:]] = False
    lists = [np.where(x)[0].tolist() for x in X]; init = [((i * NS) // K + (rr * NS) // (K * RST)) % NS for rr in range(RST) for i in range(K)]
    words = [NS]
    for l in lists: words += [len(l)] + l
    words += init; open(os.path.join(HERE, "cluster_in.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
    res = subprocess.run("vvp -n /tmp/cl.vvp | grep ^cycles", shell=True, cwd=HERE, capture_output=True, text=True)
    out = open(os.path.join(HERE, "cluster_out.txt")).read().split("\n"); tot = int(out[0].split()[1]); g = np.array([int(l.split()[1]) for l in out[1:] if l.startswith("G")])
    a, t = cross_modal.kmeans_int(X, K, ITER, RST, return_total=True); d = int(tot != t) + int((g != a).sum()); bad += d
    print(f"K={K} iterations={ITER} restarts={RST} seed={seed}: {res.stdout.strip()}; total chip {tot} model {t}; pairs differing {d}; groups used {len(set(a.tolist()))}")
print("PASS" if bad == 0 else "FAIL")
