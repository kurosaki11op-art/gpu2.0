#!/usr/bin/env python3
"""TWO SENSES (20 Oct 2026): the same check as run_check_cortex_hooks.py, but every code is a picture code (MNIST, 4,608 bits) joined with a sound code (spoken digit, 23,040 bits, FSDD) = 27,648 bits per code, so the core is built with NB = 27648 and AW = 15 (the one table over both senses). Learn / predict lines are compared bit-exactly with the integer model.
Original description: cortex_core.v built with CORTEX_HOOKS (top_margin after PREDICT, wr_count of surprise-gated table writes; 19 Oct 2026) vs the integer model (hw/brain/cortex_int.py), bit-exact.
Scenario (digits, 4,608-bit codes learned on the chip's own rule): classes 0-3 become known, LEARN clips of 0-3 in a shuffled order (some updates, some not), then PREDICT test clips of 0-4 (class 4 is unknown, so its margins are the
'novel' ones) with LOOK AGAIN off, and a second pass with only class 0 known (margin saturates). Compared: every U line (updated flag, running write count) and every P line (predicted class, top-minus-runner-up margin, write count).
usage: python run_check_cortex_hooks.py DATA_DIR [--margin=N] (N = the table update margin, default 32; 256 is the 19 Oct 2026 recommended setting)"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "brain"))
from cortex_int import CortexInt, _count, _practise  # noqa
from cortex_core import load  # noqa
import detector_learn  # noqa
import cochlea_int  # noqa
from sound_features import SoundFeatures  # noqa
sys.path.insert(0, os.path.join(HERE, '..', '..', 'brain', 'experiments', 'month4'))
from noise_floor import picture as _picture  # noqa

D = sys.argv[1]; MARGIN = int([a.split("=")[1] for a in sys.argv if a.startswith("--margin=")][0]) if any(a.startswith("--margin=") for a in sys.argv) else 32; SW = 20; SAT = (1 << (SW - 1)) - 1
xtr, ytr, xte, yte = load(D, "mnist"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
r = np.random.RandomState(3); itr = np.concatenate([r.choice(np.where(ytr == c)[0], 40, replace=False) for c in range(4)]); r.shuffle(itr); ite = r.choice(np.where(yte < 5)[0], 40, replace=False)
fes = detector_learn.learn_features(xtr[itr]); enc = lambda x: np.concatenate([g.encode(x) for g in fes], 1)
ctr, cte = enc(xtr[itr]), enc(xte[ite]); ytr, yte = ytr[itr], yte[ite]
z = np.load(os.path.join(D, "fsdd_framesums_int.npz")); Sz, sy, spk = z["S"], z["y"].astype(np.int64), z["spk"]; stest = spk == spk.max(); pic = cochlea_int.align_word(_picture(Sz, "low4x4"), 6)
CHS = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)); sf = [SoundFeatures(64, c, 3, 3, 1, 1, 4, 4).fit(pic[~stest][:12000]) for c in CHS]; aenc = lambda x: np.concatenate([f.encode(x) for f in sf], 1)
atr_all, ate_all = aenc(pic[~stest]), aenc(pic[stest]); satr, sate = sy[~stest], sy[stest]; g = np.random.RandomState(4)
heard = np.stack([atr_all[g.choice(np.where(satr == c)[0])] for c in ytr]); ctr = np.concatenate([ctr, heard], 1)               # every seen digit is paired with a heard clip of the same digit
heard_t = np.stack([ate_all[g.choice(np.where(sate == c)[0])] if (sate == c).any() else np.zeros(atr_all.shape[1], bool) for c in yte]); cte = np.concatenate([cte, heard_t], 1); NB = ctr.shape[1]; print("code bits", NB, "(picture 4608 + sound %d)" % (NB - 4608))
m = CortexInt(NB, B=10, ndream=10, night=0, daydream=0, margin=MARGIN); seeds = m.rng.copy(); cmds, exp, wr = [], [], 0
for c in range(4):
    cmds.append((5, c, [])); m.known[c] = True
for i in range(len(itr)):
    a = np.array(np.nonzero(ctr[i])[0], np.int32); cmds.append((1, int(ytr[i]), a.tolist()))
    _count(m.on, m.n, a, len(a), int(ytr[i]), m.top); u = _practise(m.W, a, len(a), int(ytr[i]), m.known, m.margin, m.cmax); wr += u; exp.append("U %d %d" % (u, wr))


def predict_lines(known_set):
    for t in range(len(ite)):
        a = np.array(np.nonzero(cte[t])[0], np.int32); cmds.append((4, 0, a.tolist()))
        s = sorted([int(m.W[c, a].astype(np.int64).sum()) for c in known_set], reverse=True); pred = max(known_set, key=lambda c: (int(m.W[c, a].astype(np.int64).sum()), -c))
        exp.append("P %d %d %d" % (pred, (s[0] - s[1]) if len(s) > 1 else SAT, wr))


predict_lines([0, 1, 2, 3])
words = []
for op, arg, lst in cmds:
    words += [op, arg, len(lst)] + list(lst)
words.append(0xFFFFFFFF)
open(os.path.join(HERE, "cmds.hex"), "w").write("\n".join("%08x" % w for w in words) + "\n"); open(os.path.join(HERE, "lanes.hex"), "w").write("\n".join("%08x" % s for s in seeds) + "\n")
subprocess.run(["iverilog", "-g2005", "-DCORTEX_HOOKS", "-o", "/tmp/hk.vvp", f"-Ptb_cortex_core_hooks.NW={len(words) + 8}", f"-Ptb_cortex_core_hooks.NB={NB}", "-Ptb_cortex_core_hooks.AW=15", f"-Ptb_cortex_core_hooks.MARGIN={MARGIN}", "cortex_core.v", "tb_cortex_core_hooks.v"], cwd=HERE, check=True)
res = subprocess.run("vvp -n /tmp/hk.vvp | grep ^commands", shell=True, cwd=HERE, capture_output=True, text=True); print((res.stdout.splitlines() or ["no summary line"])[-1].strip())
got = [g for g in open(os.path.join(HERE, "out_cortex.txt")).read().split("\n") if g and g[0] in "UP"]
bad = sum(1 for a, e in zip(got, exp) if a != e) + abs(len(got) - len(exp))
for a, e in [(a, e) for a, e in zip(got, exp) if a != e][:5]:
    print("  MISMATCH rtl:", a, " model:", e)
margins = [int(e.split()[2]) for e in exp if e.startswith("P")]; print(f"lines compared {len(exp)}, mismatches {bad}; writes {wr}; margins min {min(margins)} max {max(margins)}")
print("PASS" if bad == 0 else "FAIL")
