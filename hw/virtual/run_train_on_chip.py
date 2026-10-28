#!/usr/bin/env python3
"""TRAIN THE CHIP INSIDE THE VIRTUAL DEVICE (28 Oct 2026, SIMULATED RTL). L Cortex learns on chip: the real cortex_core.v (slow-table build) receives the command stream of a training stage (LEARN, DREAM, FOLLOW) for N clothing images and builds its own table
(fast table + dream counters + slow table); at the end every memory word is read back and compared bit for bit with the integer model (CortexSlow), and the table the chip trained is scored on the whole 10,000-image test set.
Cycles of the training are counted from the simulation (50 MHz => seconds on the virtual device). Same recipe as the shipped table (one stage, all ten classes new, one dream after every example, FOLLOW every 500 examples), images in the same shuffled order, first N of them.
Only L Cortex's table is trained here; the L Deep clause layer is trained on a host (Tsetlin feedback in numpy), not on chip.
usage: python run_train_on_chip.py N [--pipe]   -> hw/virtual/results/train_on_chip_N.json"""
import json, os, shutil, subprocess, sys, tempfile, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); CX = os.path.join(HERE, "..", "rtl", "cortex")
sys.path.insert(0, os.path.join(HERE, "..", "brain")); sys.path.insert(0, os.path.join(HERE, "..", "brain", "experiments", "month5"))
from cortex_int import CortexInt, _count, _practise, _dream  # noqa
from cortex_slow import CortexSlow, _follow  # noqa
N = int(sys.argv[1]); PIPE = ["-DCORTEX_PIPE"] if "--pipe" in sys.argv else []; NB = 4608; t0 = time.time()
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/shirt_cache.npz"); ctr, cte = z["ctr"], z["cte"]
from cortex_core import load  # noqa
_, ytr, _, yte = load("/tmp/fashion", "fashion"); ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
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



sel = np.random.RandomState(100).permutation(len(ytr))[:N]; code, y = ctr[sel], ytr[sel]
CH = 500; kw = dict(B=10, ndream=6000, night=2, daydream=1, ch=CH, K=5, FR=3, rnd=1, small="copy")
ref = CortexSlow(NB, night_stop=2, seed=1, **kw); ref.cb = 10; ref.stage(code, y)                       # the integer model's own training
m = CortexSlow(NB, night_stop=2, seed=1, **kw); m.cb = 10; seeds = m.rng.copy(); sched = CortexSlow(NB, night_stop=2, seed=1, **kw)
cmds = schedule(sched, code, y, kw["ndream"], kw["night"], 1, CH)
print("[%4.0fs] model trained; %d commands (%d LEARN, %d DREAM, %d FOLLOW, %d SCOPY)" % (time.time() - t0, len(cmds), sum(c[0] == 1 for c in cmds), sum(c[0] == 3 for c in cmds), sum(c[0] == 11 for c in cmds), sum(c[0] == 12 for c in cmds)), flush=True)
exp = execute(m, cmds)
same = bool(np.array_equal(m.W, ref.W) and np.array_equal(m.on, ref.on) and np.array_equal(m.n, ref.n) and np.array_equal(m.S, ref.S)); print("command stream reproduces the model's training exactly:", same, flush=True)
words = []
for op, arg, lst in cmds: words += [op, arg, len(lst)] + list(lst)
words.append(0xFFFFFFFF)
t = tempfile.mkdtemp(prefix="trn_", dir="/tmp")
for f in ("cortex_core.v", "tb_cortex_core_slow.v"): shutil.copy(os.path.join(CX, f), t)
tb = open(os.path.join(t, "tb_cortex_core_slow.v")).read(); tb = tb.replace("for (c = 0; c < 10; c = c + 1) $fdisplay(f, \"N", "$display(\"train_cycles %0t\", $time / 10); for (c = 0; c < 10; c = c + 1) $fdisplay(f, \"N", 1); open(os.path.join(t, "tb_cortex_core_slow.v"), "w").write(tb)
open(os.path.join(t, "cmds.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n"); open(os.path.join(t, "lanes.hex"), "w").write("\n".join("%08x" % s for s in seeds) + "\n")
subprocess.run(["iverilog", "-g2005", "-DCORTEX_SLOW", "-s", "tb_cortex_core_slow", "-o", "sim", "-Ptb_cortex_core_slow.CB=10", "-Ptb_cortex_core_slow.NW=%d" % (len(words) + 8), "cortex_core.v", "tb_cortex_core_slow.v"] + PIPE, cwd=t, check=True)
res = subprocess.run("vvp -n sim", shell=True, cwd=t, capture_output=True, text=True).stdout
tc = [int(l.split()[1]) for l in res.splitlines() if l.startswith("train_cycles")]; train_cycles = tc[0] // 1000 if tc else -1   # %0t prints picoseconds: 1 cycle = 10 ns of simulated time = 10,000 ps, and the testbench prints $time / 10 (cycles) as a time value of 1 ns = 1,000 ps per cycle
got = open(os.path.join(t, "out_cortex.txt")).read().split("\n")[:-1]; got = [g.upper() if g[0] in "WS" else g for g in got]; exp = [e.upper() if e[0] in "WS" else e for e in exp]
bad = sum(1 for a, e in zip(got, exp) if a != e) + abs(len(got) - len(exp))
for a, e in [(a, e) for a, e in zip(got, exp) if a != e][:4]: print("  MISMATCH rtl:", a, " model:", e)
Sw = [int(l.split()[1], 16) for l in got if l[0] == "S"]; assert len(Sw) == NB
Srtl = np.array([[((w >> (8 * c)) & 255) for c in range(10)] for w in Sw], np.int64); Srtl = np.where(Srtl > 127, Srtl - 256, Srtl)   # (NB, 10)
acc_rtl = float(((cte.astype(np.int32) @ Srtl).argmax(1) == yte).mean()); acc_ref = float(((cte.astype(np.int32) @ ref.S.T.astype(np.int64)).argmax(1) == yte).mean())
CLK = 50e6; shutil.rmtree(t)
r = {"images": N, "pipelined_build": bool(PIPE), "commands": len(cmds), "lines_compared": len(exp), "mismatches": int(bad), "model_stream_exact": same, "train_cycles": train_cycles, "cycles_per_image": train_cycles / N,
     "seconds_at_50MHz": train_cycles / CLK, "projected_seconds_60000_images_at_50MHz": train_cycles / N * 60000 / CLK, "test_accuracy_chip_table": acc_rtl, "test_accuracy_model_table": acc_ref, "wall_s": time.time() - t0}
os.makedirs(os.path.join(HERE, "results"), exist_ok=True); json.dump(r, open(os.path.join(HERE, "results", "train_on_chip_%d%s.json" % (N, "_pipe" if PIPE else "")), "w"), indent=1); print(json.dumps(r, indent=1))
print("PASS" if bad == 0 and same else "FAIL")
