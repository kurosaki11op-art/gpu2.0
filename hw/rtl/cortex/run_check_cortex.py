#!/usr/bin/env python3
"""cortex_core.v vs the integer reference model (hw/brain/cortex_int.py), bit-exact.

Scenario from real sensory codes (digits, 4,608-bit code): stage 1 learns classes 0/1, stage 2 learns 2/3 with dreams
of 0/1 interleaved in the day, one daydream per real example, then a night of dreams of all known classes; then
predictions on test codes. The schedule is the same one CortexInt.stage runs (checked here too). Compared: every
prediction, every update flag and dream length, and the final table, counters and counts.
Two configurations: 10-bit counters, and 5-bit counters so that synaptic scaling (halving) is exercised.
usage: python run_check_cortex.py DATA_DIR"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
from cortex_int import CortexInt, _count, _practise, _dream  # noqa
from cortex_core import load  # noqa

D = sys.argv[1]
z = np.load(os.path.join(D, "sep_mnist_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, "mnist"); ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
NB = ctr.shape[1]


def schedule(m, code, y, ndream, night, daydream):
    """the command list CortexInt.stage executes, as (op, arg, list) tuples"""
    new = sorted(set(y.tolist())); old = [c for c in np.where(m.known)[0] if c not in new]
    cmds = [(5, c, []) for c in new]
    known = sorted(set(np.where(m.known)[0].tolist()) | set(new))
    total, done, rr = ndream * len(old), 0, 0
    for i in range(len(y)):
        cmds.append((1, int(y[i]), np.nonzero(code[i])[0].tolist()))
        cmds += [(3, int(y[i]), [])] * daydream
        due = (total * (i + 1)) // len(y)
        while done < due:
            cmds.append((3, int(old[rr % len(old)]), [])); rr += 1; done += 1
    if old:
        for _ in range(night):
            cmds += [(3, int(known[j % len(known)]), []) for j in range(ndream * len(known))]
    return cmds


def execute(m, cmds):
    """run commands on the model state with the same primitives; returns the trace lines the RTL prints"""
    out, buf = [], np.zeros(NB, np.int32)
    for op, arg, lst in cmds:
        a = np.array(lst, np.int32)
        if op == 5:
            m.known[arg] = True
        elif op == 1:
            _count(m.on, m.n, a, len(a), arg, m.top); out.append("U %d" % _practise(m.W, a, len(a), arg, m.known, m.margin, m.cmax))
        elif op == 3:
            k = _dream(m.on, m.n, arg, m.rng, buf)
            out.append("D %d %d" % (k, _practise(m.W, buf, k, arg, m.known, m.margin, m.cmax)))
        elif op == 4:
            s = np.array([m.W[c, a].astype(np.int64).sum() if m.known[c] else -(1 << 40) for c in range(10)])
            out.append("P %d" % int(s.argmax()))
    out += ["N %d" % v for v in m.n]
    for b in range(NB):
        w = 0
        for c in range(10):
            w |= (int(m.W[c, b]) & 0x1F) << (5 * c)
        cw = 0
        for c in range(10):
            cw |= int(m.on[c, b]) << (m.cb * c)
        out.append("W %013x C %0*x" % (w, (10 * m.cb + 3) // 4, cw))
    return out


ok = True
for CB, n_per, ndream, night in ((10, 40, 10, 1), (5, 40, 6, 1)):
    r = np.random.RandomState(CB)
    s1 = np.concatenate([r.choice(np.where(ytr == c)[0], n_per, replace=False) for c in (0, 1)]); r.shuffle(s1)
    s2 = np.concatenate([r.choice(np.where(ytr == c)[0], n_per, replace=False) for c in (2, 3)]); r.shuffle(s2)
    tst = r.choice(np.where(yte < 4)[0], 60, replace=False)
    m = CortexInt(NB, B=CB, ndream=ndream, night=night, daydream=1); m.cb = CB
    ref = CortexInt(NB, B=CB, ndream=ndream, night=night, daydream=1)          # runs the stages the normal way
    seeds = m.rng.copy()
    cmds1 = schedule(m, ctr[s1], ytr[s1], ndream, night, 1); execute(m, cmds1)
    cmds2 = schedule(m, ctr[s2], ytr[s2], ndream, night, 1); execute(m, cmds2)
    ref.stage(ctr[s1], ytr[s1]); ref.stage(ctr[s2], ytr[s2])
    cmds_all = cmds1 + cmds2 + [(4, 0, np.nonzero(cte[t])[0].tolist()) for t in tst]
    same = np.array_equal(m.W, ref.W) and np.array_equal(m.on, ref.on) and np.array_equal(m.n, ref.n)
    print(f"CB={CB}: command schedule reproduces CortexInt.stage exactly: {same}")
    ok &= same
    # full model trace for the whole command list
    m2 = CortexInt(NB, B=CB, ndream=ndream, night=night, daydream=1); m2.cb = CB
    exp = execute(m2, cmds_all)
    words = []
    for op, arg, lst in cmds_all:
        words += [op, arg, len(lst)] + list(lst)
    words.append(0xFFFFFFFF)
    open(os.path.join(HERE, "cmds.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
    open(os.path.join(HERE, "lanes.hex"), "w").write("\n".join("%08x" % s for s in seeds) + "\n")
    subprocess.run(["iverilog", "-g2005", "-o", "/tmp/cx.vvp", f"-Ptb_cortex_core.CB={CB}", f"-Ptb_cortex_core.NW={len(words) + 8}",
                    "cortex_core.v", "tb_cortex_core.v"], cwd=HERE, check=True)
    res = subprocess.run(["vvp", "-n", "/tmp/cx.vvp"], cwd=HERE, capture_output=True, text=True)
    print(res.stdout.strip().splitlines()[-1] if res.stdout.strip() else res.stderr[-500:])
    got = open(os.path.join(HERE, "out_cortex.txt")).read().split("\n")[:-1]
    got = [g.upper() if g.startswith("W") else g for g in got]; exp = [e.upper() if e.startswith("W") else e for e in exp]
    bad = sum(1 for a, e in zip(got, exp) if a != e) + abs(len(got) - len(exp))
    for a, e in [(a, e) for a, e in zip(got, exp) if a != e][:5]:
        print("  MISMATCH rtl:", a, " model:", e)
    nP = sum(1 for e in exp if e.startswith("P")); nD = sum(1 for e in exp if e.startswith("D"))
    halved = int((m2.n < (n_per)).any()) if CB == 5 else 0
    accp = np.mean([int(e.split()[1]) == yte[t] for e, t in zip([e for e in exp if e.startswith("P")], tst)])
    print(f"CB={CB}: {len(cmds_all)} commands ({nD} dreams, {nP} predictions), lines compared {len(exp)}, "
          f"mismatches {bad}; halving exercised: {bool(halved) if CB == 5 else 'n/a'}; test accuracy on 0-3: {accp:.3f}")
    ok &= bad == 0
print("PASS" if ok else "FAIL")
