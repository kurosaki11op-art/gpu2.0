#!/usr/bin/env python3
"""cortex_core.v built with CORTEX_CONTEXT vs CortexInt(context=True) (hw/brain/cortex_int.py), bit-exact.

Scenario (digits codes): stage 1 learns 0/1; stage 2 brings 0/1 back with new examples (a new condition: the chip
freezes its dream counters, dreams old knowledge from the frozen copy during the day and alternates live / frozen at
night); stage 3 learns 2/3 the normal way; then predictions. The command schedule is checked against
CortexInt(context=True).stage, then replayed on the RTL (ops: 8 = DREAM from the frozen copy, 9 = FREEZE). Compared:
every prediction, update flag and dream length, and the final table, counters and counts.
usage: python run_check_cortex_ctx.py DATA_DIR [--asic]"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
from cortex_int import CortexInt, _count, _practise, _dream  # noqa
from cortex_core import load  # noqa

D = sys.argv[1]; ASIC = "--asic" in sys.argv
z = np.load(os.path.join(D, "sep_mnist_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, "mnist"); ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
NB = ctr.shape[1]
EXTRA = (["-DCORTEX_ASIC", "../../asic/spark_mem_sky130.v", "cortex_cg.v",
          "/opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8.v"] if ASIC else [])


def schedule(m, code, y, ndream, night, daydream):
    """the command list CortexInt(context=True).stage executes, as (op, arg, list) tuples; updates m.known"""
    new = sorted(set(y.tolist()))
    use_f = bool(m.known[new].any())
    old = list(np.where(m.known)[0]) if use_f else [c for c in np.where(m.known)[0] if c not in new]
    cmds = ([(9, 0, [])] if use_f else []) + [(5, c, []) for c in new]
    for c in new:
        m.known[c] = True
    known = list(np.where(m.known)[0])
    total, done, rr = ndream * len(old), 0, 0
    for i in range(len(y)):
        cmds.append((1, int(y[i]), np.nonzero(code[i])[0].tolist()))
        cmds += [(3, int(y[i]), [])] * daydream
        due = (total * (i + 1)) // len(y)
        while done < due:
            cmds.append((8 if use_f else 3, int(old[rr % len(old)]), [])); rr += 1; done += 1
    if old:
        for _ in range(night):
            cmds += [(8 if use_f and (j // len(known)) % 2 == 1 else 3, int(known[j % len(known)]), [])
                     for j in range(ndream * len(known))]
    return cmds


def execute(m, cmds, trace=True):
    out, buf = [], np.zeros(NB, np.int32); fon, fn = m.on.copy(), m.n.copy()
    for op, arg, lst in cmds:
        a = np.array(lst, np.int32)
        if op == 9:
            fon, fn = m.on.copy(), m.n.copy()
        elif op == 5:
            m.known[arg] = True
        elif op == 1:
            _count(m.on, m.n, a, len(a), arg, m.top); out.append("U %d" % _practise(m.W, a, len(a), arg, m.known, m.margin, m.cmax))
        elif op in (3, 8):
            k = _dream(fon, fn, arg, m.rng, buf) if op == 8 else _dream(m.on, m.n, arg, m.rng, buf)
            out.append("D %d %d" % (k, _practise(m.W, buf, k, arg, m.known, m.margin, m.cmax)))
        elif op == 4:
            s = np.array([m.W[c, a].astype(np.int64).sum() if m.known[c] else -(1 << 40) for c in range(10)])
            out.append("P %d" % int(s.argmax()))
    if not trace:
        return out
    out += ["N %d" % v for v in m.n]
    for b in range(NB):
        w = sum((int(m.W[c, b]) & 0x1F) << (5 * c) for c in range(10))
        cw = sum(int(m.on[c, b]) << (m.cb * c) for c in range(10))
        out.append("W %013x C %0*x" % (w, (10 * m.cb + 3) // 4, cw))
    return out


ok = True
for CB, n_per, ndream, night in ((10, 12, 3, 1), (5, 20, 2, 1), (10, 30, 12, 2)):
    r = np.random.RandomState(CB)
    pick = lambda cls: np.concatenate([r.choice(np.where(ytr == c)[0], n_per, replace=False) for c in cls])
    s1, s2, s3 = pick((0, 1)), pick((0, 1)), pick((2, 3))
    for s in (s1, s2, s3):
        r.shuffle(s)
    tst = r.choice(np.where(yte < 4)[0], 20, replace=False)
    kw = dict(B=CB, ndream=ndream, night=night, daydream=1, context=True)
    m = CortexInt(NB, **kw); m.cb = CB; ref = CortexInt(NB, **kw); seeds = m.rng.copy()
    sched = CortexInt(NB, **kw)                                    # tracks known classes while building the schedule
    cmds = []
    for s in (s1, s2, s3):
        cmds += schedule(sched, ctr[s], ytr[s], ndream, night, 1)
        ref.stage(ctr[s], ytr[s])
    execute(m, cmds, trace=False)
    same = np.array_equal(m.W, ref.W) and np.array_equal(m.on, ref.on) and np.array_equal(m.n, ref.n)
    nf = sum(1 for c in cmds if c[0] == 8); nz = sum(1 for c in cmds if c[0] == 9)
    print(f"CB={CB}: schedule reproduces CortexInt(context=True).stage exactly: {same} ({nz} freeze, {nf} frozen dreams)")
    ok &= same
    cmds_all = cmds + [(4, 0, np.nonzero(cte[t])[0].tolist()) for t in tst]
    m2 = CortexInt(NB, **kw); m2.cb = CB
    exp = execute(m2, cmds_all)
    words = []
    for op, arg, lst in cmds_all:
        words += [op, arg, len(lst)] + list(lst)
    words.append(0xFFFFFFFF)
    open(os.path.join(HERE, "cmds.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
    open(os.path.join(HERE, "lanes.hex"), "w").write("\n".join("%08x" % s for s in seeds) + "\n")
    subprocess.run(["iverilog", "-g2005", "-DCORTEX_CONTEXT", "-s", "tb_cortex_core_ctx", "-o", "/tmp/cxc.vvp",
                    f"-Ptb_cortex_core_ctx.CB={CB}", f"-Ptb_cortex_core_ctx.NW={len(words) + 8}",
                    "cortex_core.v", "tb_cortex_core_ctx.v"] + EXTRA, cwd=HERE, check=True)
    res = subprocess.run(["vvp", "-n", "/tmp/cxc.vvp"], cwd=HERE, capture_output=True, text=True)
    print(res.stdout.strip().splitlines()[-1] if res.stdout.strip() else res.stderr[-500:])
    got = open(os.path.join(HERE, "out_cortex.txt")).read().split("\n")[:-1]
    got = [g.upper() if g.startswith("W") else g for g in got]; exp = [e.upper() if e.startswith("W") else e for e in exp]
    bad = sum(1 for a, e in zip(got, exp) if a != e) + abs(len(got) - len(exp))
    for a, e in [(a, e) for a, e in zip(got, exp) if a != e][:5]:
        print("  MISMATCH rtl:", a, " model:", e)
    print(f"CB={CB}{' (ASIC macros)' if ASIC else ''}: {len(cmds_all)} commands, lines compared {len(exp)}, mismatches {bad}")
    ok &= bad == 0
print("PASS" if ok else "FAIL")
