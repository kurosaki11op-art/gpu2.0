#!/usr/bin/env python3
"""cortex_core.v built with CORTEX_SLOW (slow consolidating table, Redesign 6) vs CortexSlow (hw/brain/cortex_slow.py), bit-exact.

Scenario (digits codes): stage 1 learns 0/1/2 (n_per examples each: FOLLOW runs every CH ticks), stage 2 learns 3/4 from k examples each (a stage
shorter than 2*CH: SCOPY at its end), stage 3 learns 5; then predictions with the slow table. The command schedule (KNOWN, LEARN, DREAM,
FOLLOW = op 11, SCOPY = op 12) is checked against CortexSlow.stage, then replayed on the RTL. Compared: every prediction, update flag and dream
length, and the final table, counters, counts and every slow-table word.
usage: python run_check_cortex_slow.py DATA_DIR [--asic] [--pipe]"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
from cortex_int import CortexInt, _count, _practise, _dream  # noqa
from cortex_slow import CortexSlow, _follow  # noqa
from cortex_core import load  # noqa

D = sys.argv[1]; ASIC = "--asic" in sys.argv; PIPE = ["-DCORTEX_PIPE"] if "--pipe" in sys.argv else []
z = np.load(os.path.join(D, "sep_mnist_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, "mnist"); ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
NB = ctr.shape[1]
EXTRA = (["-DCORTEX_ASIC", "../../asic/spark_mem_sky130.v", "cortex_cg.v",
          "/opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8.v"] if ASIC else [])


def schedule(m, code, y, ndream, night, daydream, ch):
    """the command list CortexSlow.stage executes (tick counter m.tick), as (op, arg, list) tuples; updates m.known"""
    new = sorted(set(y.tolist()))
    old = [c for c in np.where(m.known)[0] if c not in new]
    cmds = [(5, c, []) for c in new]
    for c in new:
        m.known[c] = True
    known = list(np.where(m.known)[0])
    total, done, rr = ndream * len(old), 0, 0
    for i in range(len(y)):
        cmds.append((1, int(y[i]), np.nonzero(code[i])[0].tolist()))
        cmds += [(3, int(y[i]), [])] * daydream
        due = (total * (i + 1)) // len(y)
        while done < due:
            cmds.append((3, int(old[rr % len(old)]), [])); rr += 1; done += 1
        m.tick += 1
        if m.tick % ch == 0:
            cmds.append((11, 0, []))
    if old:
        for _ in range(night):
            for j in range(ndream * len(known)):
                cmds.append((3, int(known[j % len(known)]), [])); m.tick += 1
                if m.tick % ch == 0:
                    cmds.append((11, 0, []))
    if len(y) < 2 * ch:
        cmds.append((12, 0, []))
    return cmds


def execute(m, cmds, trace=True):
    out, buf = [], np.zeros(NB, np.int32); acc = np.zeros(10, np.int64)
    for op, arg, lst in cmds:
        a = np.array(lst, np.int32)
        if op == 5:
            m.known[arg] = True
        elif op == 1:
            _count(m.on, m.n, a, len(a), arg, m.top); out.append("U %d" % _practise(m.W, a, len(a), arg, m.known, m.margin, m.cmax))
        elif op == 3:
            k = _dream(m.on, m.n, arg, m.rng, buf)
            out.append("D %d %d" % (k, _practise(m.W, buf, k, arg, m.known, m.margin, m.cmax)))
        elif op == 11:
            _follow(m.S, m.W, m.K, m.FR, m.RND)
        elif op == 12:
            m.S[:] = m.W.astype(np.int32) << m.FR
        elif op == 4:
            if arg == 0:
                acc[:] = 0
            acc += np.array([m.S[c, a].astype(np.int64).sum() for c in range(10)])
            s = np.where(m.known, acc, -(1 << 40)); out.append("P %d" % int(s.argmax()))
    if not trace:
        return out
    out += ["N %d" % v for v in m.n]
    for b in range(NB):
        w = sum((int(m.W[c, b]) & 0x1F) << (5 * c) for c in range(10))
        cw = sum(int(m.on[c, b]) << (m.cb * c) for c in range(10))
        out.append("W %013x C %0*x" % (w, (10 * m.cb + 3) // 4, cw))
    for b in range(NB):
        sw = sum((int(m.S[c, b]) & 0xFF) << (8 * c) for c in range(10))
        out.append("S %020x" % sw)
    return out


ok = True
for CB, n_per, k_new, ndream, night, ch in ((10, 12, 1, 3, 1, 5), (5, 20, 3, 2, 1, 7), (10, 30, 5, 12, 2, 9)):
    r = np.random.RandomState(CB + ch)
    pick = lambda cls: np.concatenate([r.choice(np.where(ytr == c)[0], n_per, replace=False) for c in cls])
    s1 = pick((0, 1, 2)); s2 = np.concatenate([r.choice(np.where(ytr == c)[0], k_new, replace=False) for c in (3, 4)])
    s3 = r.choice(np.where(ytr == 5)[0], 1, replace=False)
    for s in (s1, s2, s3):
        r.shuffle(s)
    tst = r.choice(np.where(yte < 6)[0], 30, replace=False)
    kw = dict(B=CB, ndream=ndream, night=night, daydream=1, ch=ch, K=5, FR=3, rnd=1, small="copy")
    m = CortexSlow(NB, **kw); m.cb = CB; ref = CortexSlow(NB, **kw); seeds = m.rng.copy()
    sched = CortexSlow(NB, **kw)
    cmds = []
    for s in (s1, s2, s3):
        cmds += schedule(sched, ctr[s], ytr[s], ndream, night, 1, ch)
        ref.stage(ctr[s], ytr[s])
    execute(m, cmds, trace=False)
    same = (np.array_equal(m.W, ref.W) and np.array_equal(m.on, ref.on) and np.array_equal(m.n, ref.n) and np.array_equal(m.S, ref.S))
    nf = sum(1 for c in cmds if c[0] == 11); nc = sum(1 for c in cmds if c[0] == 12)
    print(f"CB={CB} CH={ch}: schedule reproduces CortexSlow.stage exactly: {same} ({nf} FOLLOW, {nc} SCOPY commands)")
    ok &= same
    cmds_all = cmds + [(4, 0, np.nonzero(cte[t])[0].tolist()) for t in tst]
    for g in range(6):                                              # LOOK AGAIN: 3-5 views summed per decision
        views = r.choice(len(cte), 3 + g % 3, replace=False)
        cmds_all += [(4, 0 if q == 0 else 1, np.nonzero(cte[v])[0].tolist()) for q, v in enumerate(views)]
    m2 = CortexSlow(NB, **kw); m2.cb = CB
    exp = execute(m2, cmds_all)
    words = []
    for op, arg, lst in cmds_all:
        words += [op, arg, len(lst)] + list(lst)
    words.append(0xFFFFFFFF)
    open(os.path.join(HERE, "cmds.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
    open(os.path.join(HERE, "lanes.hex"), "w").write("\n".join("%08x" % s for s in seeds) + "\n")
    subprocess.run(["iverilog", "-g2005", "-DCORTEX_SLOW", "-s", "tb_cortex_core_slow", "-o", "/tmp/cxs.vvp",
                    f"-Ptb_cortex_core_slow.CB={CB}", f"-Ptb_cortex_core_slow.NW={len(words) + 8}",
                    "cortex_core.v", "tb_cortex_core_slow.v"] + EXTRA + PIPE, cwd=HERE, check=True)
    res = subprocess.run(f"vvp -n /tmp/cxs.vvp | grep ^commands", shell=True, cwd=HERE, capture_output=True, text=True)
    last = res.stdout.splitlines()
    print(last[-1].strip() if last else "simulation printed no summary line")
    got = open(os.path.join(HERE, "out_cortex.txt")).read().split("\n")[:-1]
    got = [g.upper() if g[0] in "WS" else g for g in got]; exp = [e.upper() if e[0] in "WS" else e for e in exp]
    bad = sum(1 for a, e in zip(got, exp) if a != e) + abs(len(got) - len(exp))
    for a, e in [(a, e) for a, e in zip(got, exp) if a != e][:5]:
        print("  MISMATCH rtl:", a, " model:", e)
    print(f"CB={CB}{' (ASIC macros)' if ASIC else ''}: {len(cmds_all)} commands, lines compared {len(exp)}, mismatches {bad}")
    ok &= bad == 0
print("PASS" if ok else "FAIL")
