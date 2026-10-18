#!/usr/bin/env python3
"""cortex_core.v built with CORTEX_EMBED (table-score embedding for new words, Redesign 8) vs CortexEmbed (hw/brain/cortex_embed.py), bit-exact.

Scenario (digit codes, 4,608 bits): the table learns the known digits 0-5 (LEARN, n_per clips each); old words 0-2 are enrolled as KOLD = 2 prototypes each by competitive learning (PREDICT, WINNER, ENROLL with shift 5),
new words 6-8 as one prototype each from k clips (PREDICT, ENROLL with shift 0, a running mean); then test clips are matched (PREDICT, MATCH). Compared: every table update flag, prediction, WINNER slot, MATCH slot / label / distance,
and at the end the table, counters, counts, every prototype element, and every slot's filled flag / label / count.
usage: python run_check_cortex_embed.py DATA_DIR [--asic] [--pipe]"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
from cortex_int import _count, _practise  # noqa
from cortex_embed import CortexEmbed  # noqa
from cortex_core import load  # noqa

D = sys.argv[1]; ASIC = "--asic" in sys.argv; PIPE = ["-DCORTEX_PIPE"] if "--pipe" in sys.argv else []
z = np.load(os.path.join(D, "sep_mnist_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, "mnist"); ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
NB = ctr.shape[1]; NPS = 48; C = 10
EXTRA = (["-DCORTEX_ASIC", "../../asic/spark_mem_sky130.v", "cortex_cg.v",
          "/opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8.v"] if ASIC else [])
ENR = lambda slot, sh, lab: slot | (sh << 6) | (lab << 9)


def plan(n_per, k, kold, rng, m):
    """run the model while building the RTL command list: the host chooses the winner slot from the model's WINNER answer and issues ENROLL with it"""
    cmds, out = [], []

    def predict(a):
        sc = np.where(m.known, np.array([int(m.W[c, a].astype(np.int64).sum()) for c in range(m.W.shape[0])]), -(1 << 40)); out.append("P %d" % int(sc.argmax()))
        return m.embedding(a)
    for c in range(6):
        cmds.append((5, c, [])); m.known[c] = True
    for c in range(6):
        for i in rng.choice(np.where(ytr == c)[0], n_per, replace=False):
            a = np.array(np.nonzero(ctr[i])[0], np.int32); cmds.append((1, c, a.tolist()))
            _count(m.on, m.n, a, len(a), c, m.top); out.append("U %d" % _practise(m.W, a, len(a), c, m.known, m.margin, m.cmax))
    for c in range(3):                                                    # old words: competitive learning, kold slots each
        for i in rng.choice(np.where(ytr == c)[0], n_per, replace=False):
            lst = np.nonzero(ctr[i])[0].tolist(); a = np.array(lst, np.int32); cmds.append((4, 0, lst)); e = predict(a)
            cmds.append((14, c * kold | (kold << 6), lst)); sl = m.winner(e, c * kold, kold); out.append("V %d" % sl)
            cmds.append((13, ENR(sl, 5, c), lst)); m.enroll(e, sl, c, sh=5)
    for c in range(6, 9):                                                 # new words: k clips each into one slot, running mean
        for i in rng.choice(np.where(ytr == c)[0], k, replace=False):
            lst = np.nonzero(ctr[i])[0].tolist(); a = np.array(lst, np.int32); cmds.append((4, 0, lst)); e = predict(a)
            cmds.append((13, ENR(20 + c - 6, 0, c), lst)); m.enroll(e, 20 + c - 6, c, sh=0)
    for t in rng.choice(np.where(np.isin(yte, [0, 1, 2, 6, 7, 8]))[0], 40, replace=False):
        lst = np.nonzero(cte[t])[0].tolist(); a = np.array(lst, np.int32); cmds.append((4, 0, lst)); e = predict(a)
        cmds.append((15, 0, lst)); s_, lab, d = m.match(e); out.append("M %d %d %d" % (s_, lab, d))
    return cmds, out


ok = True
for n_per, k, kold in ((8, 3, 2), (12, 4, 3), (6, 2, 2)):
    rng = np.random.RandomState(n_per * 7 + k)
    m = CortexEmbed(NB, n_cls=C, np_slots=NPS, seed=1); seeds = m.rng.copy()
    cmds, exp = plan(n_per, k, kold, rng, m)
    for s_ in range(NPS * 16):
        exp.append("E %d" % (int(m.pv[s_ // 16, s_ % 16]) if s_ % 16 < C else 0))
    for s_ in range(NPS):
        exp.append("T %05x" % ((int(m.pfill[s_]) << 12) | (int(m.plab[s_]) << 8) | int(m.pn[s_])))
    words = []
    for op, arg, lst in cmds:
        words += [op, arg, len(lst)] + list(lst)
    words.append(0xFFFFFFFF)
    open(os.path.join(HERE, "cmds.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
    open(os.path.join(HERE, "lanes.hex"), "w").write("\n".join("%08x" % x for x in seeds) + "\n")
    subprocess.run(["iverilog", "-g2005", "-DCORTEX_EMBED", "-s", "tb_cortex_core_embed", "-o", "/tmp/cxe.vvp", f"-Ptb_cortex_core_embed.NW={len(words) + 8}",
                    "cortex_core.v", "tb_cortex_core_embed.v"] + EXTRA + PIPE, cwd=HERE, check=True)
    res = subprocess.run("vvp -n /tmp/cxe.vvp | grep ^commands", shell=True, cwd=HERE, capture_output=True, text=True); print(res.stdout.strip() or "no summary")
    got = open(os.path.join(HERE, "out_cortex.txt")).read().split("\n")[:-1]
    got = [g for g in got if g[0] in "UPVMET"]
    # the testbench prints P for op 4 (prediction), U for LEARN, V for WINNER, M for MATCH; drop the table dump lines (N, W)
    bad = sum(1 for a, e in zip(got, exp) if a != e) + abs(len(got) - len(exp))
    for a, e in [(a, e) for a, e in zip(got, exp) if a != e][:5]: print("  MISMATCH rtl:", a, " model:", e)
    print(f"n_per={n_per} k={k} kold={kold}: {len(cmds)} commands, lines compared {len(exp)}, mismatches {bad}")
    ok &= bad == 0
print("PASS" if ok else "FAIL")
