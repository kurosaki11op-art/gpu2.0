#!/usr/bin/env python3
"""The node: raw senses to a whole learning stage on one chip (22 Oct 2026). cortex_node_top = cortex_sense_top (retina + cochlea encoders, one core, slow table) + cortex_seq (stage and night sequencer). The testbench only shows each example to the senses and pulses ex_valid with the label;
the sequencer issues every KNOWN, LEARN (with the code length the senses report), daydream, interleaved old-class dream, FOLLOW, night dream and SCOPY. Compared with CortexSlow.stage on the Python chain's codes (Features.encode, cochlea_int.sound_picture_int + SoundFeatures.encode at offset 4608):
every count and every fast word after 2 stages (class 0, 1 with picture + sound pairs; class 2 from pictures alone, so old classes dream and the night runs).
usage: python run_check_node.py DATA_DIR"""
import os, subprocess, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain")); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain", "experiments", "month4"))
import cochlea_int, detector_learn  # noqa
from sound_features import SoundFeatures  # noqa
from cortex_slow import CortexSlow  # noqa
from cortex_core import load  # noqa
D = sys.argv[1]; NB = 9216; CB = 10; NBS = 4608; KN = 4
xtr, ytr, xte, yte = load(D, "mnist"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); r = np.random.RandomState(3)
SP = ["george", "jackson", "lucas", "nicolas", "theo", "yweweler"]


def clip(d, sp, n):
    with wave.open(os.path.join(D, "fsdd", f"{d}_{SP[sp]}_{n}.wav")) as w:
        x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64); fs = w.getframerate()
    t = np.arange(0, len(x) - 1, fs / 16000.0); x16 = np.interp(t, np.arange(len(x)), x); out = np.zeros(16000); out[:min(16000, len(x16))] = x16[:16000]
    pk = np.abs(out).max(); out = out * (12000.0 / pk) if pk > 0 else out; return out.astype(np.int16)


# detectors: picture (4 channels x 32) from MNIST, sound (4 channels x 32) from a pool of clips of classes 0-3
fes = detector_learn.learn_features(xtr[np.isin(ytr, (0, 1))][:2000]); fes = fes[:4]
pool = np.stack([clip(d, s, n) for d in range(KN) for s in range(5) for n in range(8)]); pp = cochlea_int.sound_picture_int(pool, lead=6)
CHS = (50, 110, 170, ("on", 8)); sfs = [SoundFeatures(32, c, 3, 3, 1, 1, 4, 4).fit(pp[:12000]) for c in CHS]
# the scenario: stage 1 = classes 0 and 1, two picture + sound pairs each; stage 2 = class 2, two pictures alone
pics, clips = [], []
def add_pic(c): i = np.where(ytr == c)[0][r.randint(0, 40)]; pics.append(xtr[i]); return len(pics) - 1
def add_clip(c): clips.append(clip(c, r.randint(0, 5), r.randint(8, 50))); return len(clips) - 1
st1 = [(c, add_pic(c), add_clip(c)) for c in (0, 1) for _ in range(2)]; r.shuffle(st1); st2 = [(2, add_pic(2), None) for _ in range(2)]
P = np.stack(pics); X = np.stack(clips)
pc = np.concatenate([f.encode(P) for f in fes], 1); sp_ = cochlea_int.sound_picture_int(X, lead=6); sc = np.concatenate([f.encode(sp_) for f in sfs], 1)
def code(pi, ci):
    v = np.zeros(NB, bool)
    if pi is not None: v[:NBS] = pc[pi]
    if ci is not None: v[NBS:] = sc[ci]
    return v
ndream, night, dd, nstop = 1, 1, 1, 2
m = CortexSlow(NB, B=CB, ndream=ndream, night=night, daydream=dd, night_stop=nstop, ch=100, K=5, FR=3, rnd=1, small="copy"); seeds = m.rng.copy(); words = [2]
for stage, newmask in ((st1, 0b011), (st2, 0b100)):
    m.stage(np.stack([code(pi, ci) for _, pi, ci in stage]), np.array([c for c, _, _ in stage], np.int64))
    words += [ndream, night, dd, nstop, len(stage), newmask]
    for c, pi, ci in stage: words += [c, 0xFFFF if pi is None else pi, 0xFFFF if ci is None else ci]
exp = ["N %d" % v for v in m.n]
for b in range(NB):
    w = sum((int(m.W[c, b]) & 0x1F) << (5 * c) for c in range(10)); cw = sum(int(m.on[c, b]) << (CB * c) for c in range(10)); exp.append("W %013x C %025x" % (w, cw))
tv = [sum(1 << i for i in range(len(t)) if t[i]) for f in fes for t in (f.cnt >= 0)]; ta = [sum(1 << i for i in range(len(t)) if t[i]) for f in sfs for t in (f.cnt >= 0)]
W = lambda name, lines: open(os.path.join(HERE, name), "w").write("\n".join(lines) + "\n")
W("node_in.hex", ["%08x" % w for w in words]); W("tmpl_v.hex", ["%07x" % w for w in tv]); W("tmpl_a.hex", ["%07x" % w for w in ta]); W("lanes.hex", ["%08x" % s_ for s_ in seeds])
W("pics.hex", ["%02x" % v for v in P.reshape(-1)]); W("clips.hex", ["%04x" % (int(v) & 0xFFFF) for v in X.reshape(-1)])
subprocess.run(["iverilog", "-g2005", "-DCORTEX_SLOW", "-o", "/tmp/node.vvp", f"-Ptb_node.NPIC={len(P)}", f"-Ptb_node.NCLIP={len(X)}", f"-Ptb_node.NW={len(words) + 8}", "cortex_node_top.v", "cortex_sense_top.v", "cortex_seq.v", "cortex_core.v", "cortex_encoder_gen.v", "cortex_cochlea_stream.v", "tb_node.v"] + (["-DCORTEX_PIPE"] if "--pipe" in sys.argv else []), cwd=HERE, check=True)
res = subprocess.run("vvp -n /tmp/node.vvp | grep ^stages", shell=True, cwd=HERE, capture_output=True, text=True); print((res.stdout.splitlines() or ["no summary line"])[-1].strip())
got = [g for g in open(os.path.join(HERE, "node_out.txt")).read().split("\n") if g]
bad = sum(1 for a, e in zip(got, exp) if a != e) + abs(len(got) - len(exp))
for a, e in [(a, e) for a, e in zip(got, exp) if a != e][:5]: print("  MISMATCH rtl:", a, " model:", e)
print(f"lines compared {len(exp)}, mismatches {bad}; picture codes {pc.sum(1).mean():.0f} active, sound codes {sc.sum(1).mean():.0f} active; night dreams run in the model {int(m.stats[0])}")
print("PASS" if bad == 0 else "FAIL")
