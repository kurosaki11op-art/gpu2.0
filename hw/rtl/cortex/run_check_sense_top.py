#!/usr/bin/env python3
"""Whole two-sense chip, bit-exact (20 Oct 2026): pixels and raw 16 kHz samples -> cortex_sense_top (retina encoder 4 x 32, cochlea with noise floor and word alignment + sound encoder 4 x 32, one list, one core NB = 9,216, AW = 14)
against the Python chain: Features.encode (picture) + cochlea_int.sound_picture_int -> SoundFeatures.encode (sound, offset 4608) -> integer chip model.
Scenario: classes 0-3 become known; LEARN with picture + sound (3 pairs per class), then LEARN with the picture alone and with the sound alone (1 each per class); then PREDICT test items with both senses, with the picture alone, with the sound alone. Compared: every update flag, every prediction, the final counts, table and dream counters.
usage: python run_check_sense_top.py DATA_DIR   (needs fsdd_framesums_int.npz's source wavs in DATA_DIR/fsdd and mnist.npz)"""
import os, subprocess, sys, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain")); sys.path.insert(0, os.path.join(HERE, "..", "..", "brain", "experiments", "month4"))
import cochlea_int, detector_learn  # noqa
from sound_features import SoundFeatures  # noqa
from cortex_int import CortexInt, _count, _practise  # noqa
from cortex_core import load  # noqa
D = sys.argv[1]; NPAIR, NSOLO, NTEST = 3, 1, 8; NB = 9216; CB = 10; NBS = 4608; KN = 4
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
# the scenario's items
cls_tr = [c for c in range(KN) for _ in range(NPAIR + NSOLO * 2)]; pics, clips, labels = [], [], []
items = []                                                                                    # (kind, label, picture index, clip index)
def add_pic(c): i = np.where(ytr == c)[0][r.randint(0, 40)]; pics.append(xtr[i]); return len(pics) - 1
def add_clip(c, sp=None): clips.append(clip(c, r.randint(0, 5) if sp is None else sp, r.randint(8, 50))); return len(clips) - 1
learn = []
for c in range(KN):
    for _ in range(NPAIR): learn.append((c, add_pic(c), add_clip(c)))
    learn.append((c, add_pic(c), None)); learn.append((c, None, add_clip(c)))
r.shuffle(learn)
test = []
for k in range(NTEST):
    c = k % KN; i = np.where(yte == c)[0][r.randint(0, 40)]; pics.append(xte[i]); pi = len(pics) - 1; ci = add_clip(c, 5); test.append((c, pi, ci))
P = np.stack(pics); X = np.stack(clips)
pc = np.concatenate([f.encode(P) for f in fes], 1); sp_ = cochlea_int.sound_picture_int(X, lead=6); sc = np.concatenate([f.encode(sp_) for f in sfs], 1)
idx = lambda pi, ci: ([] if pi is None else np.nonzero(pc[pi])[0].tolist()) + ([] if ci is None else (np.nonzero(sc[ci])[0] + NBS).tolist())
m = CortexInt(NB, B=CB, ndream=0, night=0, daydream=0); seeds = m.rng.copy(); cmds, exp = [], []
for c in range(KN): cmds.append((5, c, 0xFFFF, 0xFFFF)); m.known[c] = True
for c, pi, ci in learn:
    cmds.append((1, c, 0xFFFF if pi is None else pi, 0xFFFF if ci is None else ci)); a = np.array(idx(pi, ci), np.int32)
    _count(m.on, m.n, a, len(a), c, m.top); exp.append("U %d" % _practise(m.W, a, len(a), c, m.known, m.margin, m.cmax))
for mode in ("both", "picture", "sound"):
    for c, pi, ci in test:
        pi_, ci_ = (pi if mode != "sound" else None), (ci if mode != "picture" else None); cmds.append((4, 0, 0xFFFF if pi_ is None else pi_, 0xFFFF if ci_ is None else ci_)); a = np.array(idx(pi_, ci_), np.int64)
        s = np.array([m.W[k, a].astype(np.int64).sum() if m.known[k] else -(1 << 40) for k in range(10)]); exp.append("P %d" % int(s.argmax()))
exp += ["N %d" % v for v in m.n]
for b in range(NB):
    w = sum((int(m.W[c, b]) & 0x1F) << (5 * c) for c in range(10)); cw = sum(int(m.on[c, b]) << (CB * c) for c in range(10)); exp.append("W %013x C %025x" % (w, cw))
words = [w for cm in cmds for w in cm] + [0xFFFFFFFF]
tv = [sum(1 << i for i in range(len(t)) if t[i]) for f in fes for t in (f.cnt >= 0)]; ta = [sum(1 << i for i in range(len(t)) if t[i]) for f in sfs for t in (f.cnt >= 0)]
W = lambda name, lines: open(os.path.join(HERE, name), "w").write("\n".join(lines) + "\n")
W("sense_cmds.hex", ["%08x" % w for w in words]); W("tmpl_v.hex", ["%07x" % w for w in tv]); W("tmpl_a.hex", ["%07x" % w for w in ta]); W("lanes.hex", ["%08x" % s_ for s_ in seeds])
W("pics.hex", ["%02x" % v for v in P.reshape(-1)]); W("clips.hex", ["%04x" % (int(v) & 0xFFFF) for v in X.reshape(-1)])
subprocess.run(["iverilog", "-g2005", "-o", "/tmp/sense.vvp", f"-Ptb_sense_top.NPIC={len(P)}", f"-Ptb_sense_top.NCLIP={len(X)}", f"-Ptb_sense_top.NW={len(words) + 8}", "cortex_sense_top.v", "cortex_core.v", "cortex_encoder_gen.v", "cortex_cochlea_stream.v", "tb_sense_top.v"], cwd=HERE, check=True)
res = subprocess.run("vvp -n /tmp/sense.vvp | grep ^commands", shell=True, cwd=HERE, capture_output=True, text=True); print((res.stdout.splitlines() or ["no summary line"])[-1].strip())
got = open(os.path.join(HERE, "sense_out.txt")).read().split("\n"); got = [g for g in got if g]
bad = sum(1 for a, e in zip(got, exp) if a != e) + abs(len(got) - len(exp))
for a, e in [(a, e) for a, e in zip(got, exp) if a != e][:5]: print("  MISMATCH rtl:", a, " model:", e)
npred = sum(1 for e in exp if e[0] == "P"); right = sum(1 for g, (c, pi, ci) in zip([g for g in got if g[0] == "P"], test * 3) if int(g.split()[1]) == c)
print(f"lines compared {len(exp)}, mismatches {bad}; picture codes {pc.sum(1).mean():.0f} active, sound codes {sc.sum(1).mean():.0f} active; predictions right {right}/{npred}")
print("PASS" if bad == 0 else "FAIL")
