#!/usr/bin/env python3
"""cortex_seq.v (the stage and night sequencer) driving cortex_core.v (CORTEX_SLOW) vs CortexSlow.stage (hw/brain/cortex_slow.py), bit-exact (22 Oct 2026). The testbench only loads each example's code list and pulses ex_valid;
the sequencer issues every KNOWN, LEARN, DREAM, FOLLOW and SCOPY command, runs the night and its early stop. Compared after 3 stages (the third shorter than 2 * CH, so SCOPY runs): every count, fast word and slow word.
Synthetic class-clustered codes (256 bits), several parameter sets (early stop off / on, 1-2 daydreams, margin 32 and 256). usage: python run_check_seq.py [--pipe]"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
from cortex_slow import CortexSlow  # noqa
NB = 256; ok = True; PIPE = ["-DCORTEX_PIPE"] if "--pipe" in sys.argv else []
for ndream, night, dd, ch, nstop, margin, seed in ((4, 2, 1, 10, 0, 32, 1), (40, 2, 1, 12, 1, 256, 2), (6, 1, 2, 7, 2, 32, 3), (40, 3, 1, 9, 3, 256, 4)):
    r = np.random.RandomState(seed); T = r.rand(10, NB) < 0.12
    def ex(c, n): return [np.nonzero(T[c] ^ (r.rand(NB) < 0.06))[0].tolist() for _ in range(n)]
    stages = [((0, 1), 15), ((2, 3), 12), ((4,), 8)]; data = []
    for cls, per in stages:
        items = [(c, l) for c in cls for l in ex(c, per)]; r.shuffle(items); data.append(items)
    kw = dict(B=10, ndream=ndream, night=night, daydream=dd, ch=ch, K=5, FR=3, rnd=1, small="copy", night_stop=nstop, margin=margin)
    m = CortexSlow(NB, **kw); seeds = m.rng.copy(); words = [len(stages)]
    for (cls, per), items in zip(stages, data):
        code = np.zeros((len(items), NB), bool)
        for i, (c, l) in enumerate(items): code[i, l] = True
        m.stage(code, np.array([c for c, _ in items], np.int64))
        words += [ndream, night, dd, ch, nstop, len(items), sum(1 << c for c in cls)]
        for c, l in items: words += [c, len(l)] + l
    open(os.path.join(HERE, "seq_in.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n"); open(os.path.join(HERE, "lanes.hex"), "w").write("\n".join("%08x" % s for s in seeds) + "\n")
    exp = ["N %d" % v for v in m.n]
    for b in range(NB):
        w = sum((int(m.W[c, b]) & 0x1F) << (5 * c) for c in range(10)); cw = sum(int(m.on[c, b]) << (10 * c) for c in range(10)); exp.append("W %013x C %0*x" % (w, (100 + 3) // 4, cw))
    for b in range(NB): exp.append("S %020x" % sum((int(m.S[c, b]) & 0xFF) << (8 * c) for c in range(10)))
    subprocess.run(["iverilog", "-g2005", "-DCORTEX_SLOW", "-s", "tb_seq", "-o", "/tmp/seq.vvp", f"-Ptb_seq.MARGIN={margin}", f"-Ptb_seq.NW={len(words) + 16}", "cortex_core.v", "cortex_seq.v", "tb_seq.v"] + PIPE, cwd=HERE, check=True)
    res = subprocess.run("timeout 900 vvp -n /tmp/seq.vvp | grep ^stages", shell=True, cwd=HERE, capture_output=True, text=True)
    got = open(os.path.join(HERE, "out_cortex.txt")).read().split("\n")[:-1]
    got = [g.upper() if g[0] in "WS" else g for g in got]; exp = [e.upper() if e[0] in "WS" else e for e in exp]
    bad = sum(1 for a, e in zip(got, exp) if a != e) + abs(len(got) - len(exp))
    for a, e in [(a, e) for a, e in zip(got, exp) if a != e][:4]: print("  MISMATCH rtl:", a, " model:", e)
    print(f"ndream={ndream} night={night} daydream={dd} ch={ch} night_stop={nstop} margin={margin}: {res.stdout.strip()}; night dreams run in the model {int(m.stats[0])}; lines compared {len(exp)}, mismatches {bad}")
    ok &= bad == 0
print("PASS" if ok else "FAIL")
