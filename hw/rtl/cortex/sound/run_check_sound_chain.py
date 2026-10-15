#!/usr/bin/env python3
"""Whole sound chip, bit-exact: raw 16 kHz samples -> cortex_cochlea (noise floor) -> cortex_encoder_gen (10 x 64)
-> cortex_core (NB 23,040), against the Python chain cochlea_int -> Features.encode -> integer chip model.
Scenario: stage 1 learns words 0/1 from raw clips, stage 2 learns words 2/3 with dreams of 0/1 (one daydream per
example, interleaved dreams, a night), then the chip hears test clips and predicts. Compared: every update flag,
dream length and prediction, and the final table, dream counters and counts. usage: python run_check_sound_chain.py DATA_DIR"""
import os, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "brain"))
import cochlea, cochlea_int  # noqa
from feature_layer import Features  # noqa
from cortex_int import CortexInt, _count, _practise, _dream  # noqa
D = sys.argv[1]; NPER, NDREAM, NIGHT, NTEST = 2, 2, 1, 4
NB = 23040; CB = 10
# detectors: learned (on the PC here) from stage-1 sound pictures of the integer cochlea with its noise floor
z = np.load(os.path.join(D, "speech_framesums_int.npz")); S, y, te = z["S"], z["y"], z["te"]
v = cochlea_int.noise_floor(S); e = np.floor(np.log2(v)).astype(np.int64)
lg = 4 * e + ((v >> np.maximum(e - 2, 0)) & 3); top = lg.reshape(len(v), -1).max(1)[:, None, None]
P = np.clip(255 - (top - lg) * 8, 0, 255).reshape(len(v), -1).astype(np.uint8)
CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
fes = [Features(64, thr=c).fit(P[~te][np.isin(y[~te], (0, 1))][:12000]) for c in CH]
# raw clips for the scenario
root = os.path.join(D, "speech"); r = np.random.RandomState(7); clips, labels = [], []
def pick(word, k):
    fs = sorted(os.listdir(os.path.join(root, cochlea.WORDS[word])))
    return [cochlea.read(os.path.join(root, cochlea.WORDS[word], fs[j])) for j in r.choice(len(fs), k, replace=False)]
order = []
for stage in ((0, 1), (2, 3)):
    idx = []
    for w in stage:
        for x in pick(w, NPER):
            clips.append(x); labels.append(w); idx.append(len(clips) - 1)
    r.shuffle(idx); order.append(idx)
test = []
for k in range(NTEST):
    clips.append(pick(k % 4, 1)[0]); labels.append(k % 4); test.append(len(clips) - 1)
X = np.stack(clips).astype(np.int16)
codes = np.concatenate([f.encode(cochlea_int.sound_picture_int(X)) for f in fes], 1)
# command schedule (as CortexInt.stage runs it) and the model trace
m = CortexInt(NB, B=CB, ndream=NDREAM, night=NIGHT, daydream=1); m.cb = CB; seeds = m.rng.copy()
ref = CortexInt(NB, B=CB, ndream=NDREAM, night=NIGHT, daydream=1)
cmds, out, buf = [], [], np.zeros(NB, np.int32)
for idx in order:
    yy = [labels[i] for i in idx]; new = sorted(set(yy)); old = [c for c in np.where(m.known)[0] if c not in new]
    cmds += [(5, c, 0xFFFF) for c in new]
    for c in new:
        m.known[c] = True
    kn = list(np.where(m.known)[0]); total, done, rr = NDREAM * len(old), 0, 0
    for j, i in enumerate(idx):
        cmds.append((1, labels[i], i)); cmds.append((3, labels[i], 0xFFFF))
        due = (total * (j + 1)) // len(idx)
        while done < due:
            cmds.append((3, int(old[rr % len(old)]), 0xFFFF)); rr += 1; done += 1
    if old:
        for _ in range(NIGHT):
            cmds += [(3, int(kn[q % len(kn)]), 0xFFFF) for q in range(NDREAM * len(kn))]
    ref.stage(codes[idx], np.array(yy))
cmds += [(4, 0, i) for i in test]
m = CortexInt(NB, B=CB, ndream=NDREAM, night=NIGHT, daydream=1); m.cb = CB
for op, arg, clip in cmds:
    if op == 5:
        m.known[arg] = True
    elif op == 1:
        a = np.nonzero(codes[clip])[0].astype(np.int32); _count(m.on, m.n, a, len(a), arg, m.top)
        out.append("U %d" % _practise(m.W, a, len(a), arg, m.known, m.margin, m.cmax))
    elif op == 3:
        k = _dream(m.on, m.n, arg, m.rng, buf); out.append("D %d %d" % (k, _practise(m.W, buf, k, arg, m.known, m.margin, m.cmax)))
    elif op == 4:
        a = np.nonzero(codes[clip])[0]
        s = np.array([m.W[c, a].astype(np.int64).sum() if m.known[c] else -(1 << 40) for c in range(10)]); out.append("P %d" % int(s.argmax()))
same = np.array_equal(m.W, ref.W) and np.array_equal(m.on, ref.on) and np.array_equal(m.n, ref.n)
print("schedule reproduces CortexInt.stage exactly:", same)
out += ["N %d" % v_ for v_ in m.n]
for b in range(NB):
    w = sum((int(m.W[c, b]) & 0x1F) << (5 * c) for c in range(10)); cw = sum(int(m.on[c, b]) << (CB * c) for c in range(10))
    out.append("W %013x C %025x" % (w, cw))
# files for the testbench
words = [sum(1 << i for i in range(25) if t[i]) for f in fes for t in (f.cnt >= 0)]
open(os.path.join(HERE, "tmpl.hex"), "w").write("\n".join("%07x" % w for w in words) + "\n")
open(os.path.join(HERE, "clips.hex"), "w").write("\n".join("%04x" % (int(v_) & 0xFFFF) for v_ in X.reshape(-1)) + "\n")
open(os.path.join(HERE, "lanes.hex"), "w").write("\n".join("%08x" % s for s in seeds) + "\n")
cw = []
for op, arg, clip in cmds:
    cw += [op, arg, clip]
cw.append(0xFFFFFFFF)
open(os.path.join(HERE, "sound_cmds.hex"), "w").write("\n".join("%08x" % w for w in cw) + "\n")
R = os.path.join(HERE, "..")
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/snd.vvp", f"-Ptb_sound_chain.NCLIP={len(clips)}", f"-Ptb_sound_chain.NW={len(cw) + 8}",
                os.path.join(R, "cortex_sound_top.v"), os.path.join(R, "cortex_cochlea.v"), os.path.join(R, "cortex_encoder_gen.v"),
                os.path.join(R, "cortex_core.v"), "tb_sound_chain.v", f"-I{R}"], cwd=HERE, check=True)
res = subprocess.run("vvp -n /tmp/snd.vvp | grep ^commands", shell=True, cwd=HERE, capture_output=True, text=True)
print(res.stdout.strip())
got = open(os.path.join(HERE, "sound_out.txt")).read().split("\n")[:-1]
got = [g.upper() if g.startswith("W") else g for g in got]; exp = [e_.upper() if e_.startswith("W") else e_ for e_ in out]
bad = sum(1 for a_, e_ in zip(got, exp) if a_ != e_) + abs(len(got) - len(exp))
for a_, e_ in [(a_, e_) for a_, e_ in zip(got, exp) if a_ != e_][:5]:
    print("  MISMATCH rtl:", a_, " model:", e_)
preds = [int(l.split()[1]) for l in exp if l.startswith("P")]
print(f"{len(cmds)} commands ({len(clips)} raw clips heard), lines compared {len(exp)}, mismatches {bad}; "
      f"test predictions {preds} for words {[labels[i] for i in test]}")
for fn in ("clips.hex", "sound_out.txt"):
    os.remove(os.path.join(HERE, fn))
print("PASS" if bad == 0 and same else "FAIL")
