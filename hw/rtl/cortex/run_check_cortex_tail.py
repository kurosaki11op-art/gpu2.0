#!/usr/bin/env python3
"""TAIL MEMORY (21 Oct 2026): cortex_core.v built with CORTEX_CONTEXT (the frozen-copy memory doubles as the tail memory; op 0 = TAILCOUNT, op 8 = DREAM from it) vs the model, bit-exact. Replaces nothing: run_check_cortex_ctx.py still checks the frozen-copy use.

Old scenario text (digits codes): stage 1 learns 0/1; stage 2 brings 0/1 back with new examples (a new condition: the chip
freezes its dream counters, dreams old knowledge from the frozen copy during the day and alternates live / frozen at
night); stage 3 learns 2/3 the normal way; then predictions. The command schedule is checked against
CortexInt(context=True).stage, then replayed on the RTL (ops: 8 = DREAM from the frozen copy, 9 = FREEZE). Compared:
every prediction, update flag and dream length, and the final table, counters and counts.
usage: python run_check_cortex_ctx.py DATA_DIR [--asic] [--pipe]"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
from cortex_int import CortexInt, _count, _practise, _dream  # noqa
from cortex_core import load  # noqa

D = sys.argv[1]; ASIC = "--asic" in sys.argv; PIPE = ["-DCORTEX_PIPE"] if "--pipe" in sys.argv else []
z = np.load(os.path.join(D, "sep_mnist_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
_, ytr, _, yte = load(D, "mnist"); ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
NB = ctr.shape[1]
EXTRA = (["-DCORTEX_ASIC", "../../asic/spark_mem_sky130.v", "cortex_cg.v",
          "/opt/sky130_sram_macros/sky130_sram_2kbyte_1rw1r_32x512_8/sky130_sram_2kbyte_1rw1r_32x512_8.v"] if ASIC else [])


def run_model(m, ont, nt, tc, code, y, ndream, night, daydream, mixt=3):
    """the host schedule of a stage with the tail memory (the same rule as `tailmem` in hw/brain/cortex_rules.py), executed on the model and recorded as (op, arg, list):
    op 5 KNOWN, 1 LEARN, 0 TAILCOUNT (after a LEARN whose table update wrote), 3 DREAM from the live counters, 8 DREAM from the tail memory (dream number t uses it when the class has a tail and t mod 16 < mixt), 4 PREDICT"""
    cmds, out, buf = [], [], np.zeros(NB, np.int32)
    new = sorted(set(y.tolist())); old = [c for c in np.where(m.known)[0] if c not in new]
    for c in new: m.known[c] = True; cmds.append((5, c, []))
    known = list(np.where(m.known)[0])

    def dream(c):
        use_t = nt[c] > 0 and (tc[0] & 15) < mixt; tc[0] += 1
        k = _dream(ont, nt, c, m.rng, buf) if use_t else _dream(m.on, m.n, c, m.rng, buf)
        w = _practise(m.W, buf, k, c, m.known, m.margin, m.cmax); cmds.append((8 if use_t else 3, int(c), [])); out.append("D %d %d" % (k, w))
    total, done, rr = ndream * len(old), 0, 0
    for i in range(len(y)):
        a = np.nonzero(code[i])[0].astype(np.int32); c = int(y[i]); cmds.append((1, c, a.tolist()))
        _count(m.on, m.n, a, len(a), c, m.top); w = _practise(m.W, a, len(a), c, m.known, m.margin, m.cmax); out.append("U %d" % w)
        if w > 0:
            _count(ont, nt, a, len(a), c, m.top); cmds.append((0, c, a.tolist()))
        for _ in range(daydream): dream(c)
        due = (total * (i + 1)) // len(y)
        while done < due:
            dream(old[rr % len(old)]); rr += 1; done += 1
    if old:
        for _ in range(night):
            for j in range(ndream * len(known)): dream(known[j % len(known)])
    return cmds, out


ok = True
for CB, n_per, ndream, night in ((10, 12, 3, 1), (5, 60, 4, 1)):
    r = np.random.RandomState(CB)
    pick = lambda cls: np.concatenate([r.choice(np.where(ytr == c)[0], n_per, replace=False) for c in cls])
    s1, s2, s3 = pick((0, 1)), pick((0, 1)), pick((2, 3))
    for s in (s1, s2, s3):
        r.shuffle(s)
    tst = r.choice(np.where(yte < 4)[0], 20, replace=False)
    kw = dict(B=CB, ndream=ndream, night=night, daydream=1)
    m = CortexInt(NB, **kw); m.cb = CB; seeds = m.rng.copy(); ont = np.zeros_like(m.on); nt = np.zeros(11, np.int32); tc = [0]
    cmds, exp = [], []
    for s_ in (s1, s2, s3):
        c_, o_ = run_model(m, ont, nt, tc, ctr[s_], ytr[s_], ndream, night, 1); cmds += c_; exp += o_
    n0 = sum(1 for c in cmds if c[0] == 0); nf = sum(1 for c in cmds if c[0] == 8)
    print(f"CB={CB}: {n0} tail counts, {nf} dreams from the tail memory, tail example counts {nt[:4].tolist()}")
    ok &= n0 > 0 and nf > 0
    pred = [(4, 0, np.nonzero(cte[t])[0].tolist()) for t in tst]; cmds_all = cmds + pred
    for _, _, lst in pred:
        sc = np.array([m.W[c, lst].astype(np.int64).sum() if m.known[c] else -(1 << 40) for c in range(10)]); exp.append("P %d" % int(sc.argmax()))
    exp += ["N %d" % v for v in m.n]
    for b in range(NB):
        w = sum((int(m.W[c, b]) & 0x1F) << (5 * c) for c in range(10)); cw = sum(int(m.on[c, b]) << (m.cb * c) for c in range(10))
        exp.append("W %013x C %0*x" % (w, (10 * m.cb + 3) // 4, cw))
    words = []
    for op, arg, lst in cmds_all:
        words += [op, arg, len(lst)] + list(lst)
    words.append(0xFFFFFFFF)
    open(os.path.join(HERE, "cmds.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n")
    open(os.path.join(HERE, "lanes.hex"), "w").write("\n".join("%08x" % s for s in seeds) + "\n")
    subprocess.run(["iverilog", "-g2005", "-DCORTEX_CONTEXT", "-s", "tb_cortex_core_ctx", "-o", "/tmp/cxt.vvp",
                    f"-Ptb_cortex_core_ctx.CB={CB}", f"-Ptb_cortex_core_ctx.NW={len(words) + 8}",
                    "cortex_core.v", "tb_cortex_core_ctx.v"] + EXTRA + PIPE, cwd=HERE, check=True)
    # the SRAM macro models print every access: filter the stream, keep only the summary line
    res = subprocess.run(f"vvp -n /tmp/cxt.vvp | grep ^commands", shell=True, cwd=HERE, capture_output=True, text=True)
    last = res.stdout.splitlines()
    print(last[-1].strip() if last else "simulation printed no summary line")
    got = open(os.path.join(HERE, "out_cortex.txt")).read().split("\n")[:-1]
    got = [g.upper() if g.startswith("W") else g for g in got]; exp = [e.upper() if e.startswith("W") else e for e in exp]
    bad = sum(1 for a, e in zip(got, exp) if a != e) + abs(len(got) - len(exp))
    for a, e in [(a, e) for a, e in zip(got, exp) if a != e][:5]:
        print("  MISMATCH rtl:", a, " model:", e)
    print(f"CB={CB}{' (ASIC macros)' if ASIC else ''}: {len(cmds_all)} commands, lines compared {len(exp)}, mismatches {bad}")
    ok &= bad == 0
print("PASS" if ok else "FAIL")
