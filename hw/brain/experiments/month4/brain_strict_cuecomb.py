"""Reliability-weighted cue combination (21 Oct 2026) SIMULATED. Two separate tables (picture, sound) whose class scores are combined: plain sum (joint-table equivalent), or each sense weighted by its own confidence (top-2 margin relative to its typical margin on clean training data, weight by shift). Data as brain_strict_twosense.py. (orig doc) Two senses (20 Oct 2026) SIMULATED. Vision = MNIST digits through the shipped retina code (4,608 bits); hearing = FSDD spoken digits (zero..nine, 6 speakers, 8 kHz) through the integer cochlea, noise floor, word alignment and the sound detector rule (10 channels, 23,040 bits). The two sets share only the digit class; a seen digit is paired with a heard clip of the same digit
(different instances, as a child sees a shirt while hearing the word). Chip: counting table, one pass, margin 256 / 1,500 dreams / 1 night, 3 seeds. Test speaker = the last speaker (not in training).
  A  picture learner with the TRUE labels (reference)
  B  picture learner with ZERO labels: each seen digit's label is what the ear's own classifier (trained on the labelled sound clips) says about the clip heard with it
  C  sound learner alone (labelled clips), test on the held-out speaker
  D  joint table over picture + sound bits, trained on the pairs; tested with both senses, picture only (sound blank), sound only (picture blank), and with a degraded sense: 25 % of the picture's active bits dropped, or 50 % of the sound's
usage: DATA_DIR; env NPS, SEEDS."""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cochlea_int, detector_learn
from sound_features import SoundFeatures
from noise_floor import picture as _picture
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 3)); t0 = time.time(); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, "mnist"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])]); enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fes], 1) for i in range(0, len(x), 1000)])
vtr, vte = enc(xtr), enc(xte)
z = np.load(os.path.join(D, "fsdd_framesums_int.npz")); S, sy, spk = z["S"], z["y"].astype(np.int64), z["spk"]; stest = spk == spk.max()
pic = cochlea_int.align_word(_picture(S, "low4x4"), 6); CH = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
fs = [SoundFeatures(64, c, 3, 3, 1, 1, 4, 4).fit(pic[~stest][:12000]) for c in CH]; aenc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 1000]) for f in fs], 1) for i in range(0, len(x), 1000)])
atr, ate = aenc(pic[~stest]), aenc(pic[stest]); satr, sate = sy[~stest], sy[stest]; print("vision", vtr.shape, "hearing", atr.shape, "train clips", len(satr), "test clips", len(sate), "%.0fs" % (time.time() - t0), flush=True)


def chip(nb, seed): return CortexSlow(nb, ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)


def fit(code, lab, seed):
    m = chip(code.shape[1], seed); o = np.random.RandomState(seed).permutation(len(lab)); m.stage(code[o], lab[o]); return m


acc = lambda m, c, y: float((m.predict(c) == y).mean())

def sc(m, c): return np.where(m.known[None, :], c.astype(np.int32) @ m.S.T.astype(np.int32), -(1 << 28)).astype(np.int64)
def mg(s): t = np.sort(s, 1); return t[:, -1] - t[:, -2]
R = {}
def add(k, v): R.setdefault(k, []).append(v)
for seed in range(1, SEEDS + 1):
    r = np.random.RandomState(seed); pair = np.array([r.choice(np.where(satr == d)[0]) for d in ytr]); heard = atr[pair]
    P = fit(vtr, ytr, seed); A = fit(heard, ytr, seed); joint = fit(np.concatenate([vtr, heard], 1), ytr, seed)
    mp, ma = np.median(mg(sc(P, vtr[:2000]))), np.median(mg(sc(A, heard[:2000])))
    tp = np.array([r.choice(np.where(sate == d)[0]) for d in yte]); ts = ate[tp]
    drop = lambda c, p: c & (r.rand(*c.shape) >= p)
    for name, (v, a) in {"clean": (vte, ts), "picture 25% dropped": (drop(vte, .25), ts), "picture 50% dropped": (drop(vte, .5), ts), "sound 50% dropped": (vte, drop(ts, .5)), "both 25% dropped": (drop(vte, .25), drop(ts, .25))}.items():
        sp_, sa_ = sc(P, v), sc(A, a); add(name + " | joint table", acc(joint, np.concatenate([v, a], 1), yte)); add(name + " | sum", float(((sp_ + sa_).argmax(1) == yte).mean()))
        rp, ra = mg(sp_) / mp, mg(sa_) / ma
        for gam in (1, 2):
            wp, wa = rp ** gam, ra ** gam; add(name + " | confidence weight ^%d" % gam, float(((sp_ * wp[:, None] + sa_ * wa[:, None]).argmax(1) == yte).mean()))
        for gam in (1, 2):
            ep, ea = np.clip(np.round(np.log2(np.maximum(rp, 1/16))), -4, 3).astype(int) * gam, np.clip(np.round(np.log2(np.maximum(ra, 1/16))), -4, 3).astype(int) * gam
            e0 = np.minimum(ep, ea); shp, sha = ep - e0, ea - e0                       # relative shifts only: scores shifted left, no multiply
            add(name + " | shift weights ^%d" % gam, float((((sp_ << shp[:, None]) + (sa_ << sha[:, None])).argmax(1) == yte).mean()))
        add(name + " | trust the more confident", float(np.where((rp >= ra), sp_.argmax(1), sa_.argmax(1)) == yte).mean()) if False else add(name + " | trust the more confident", float((np.where(rp >= ra, sp_.argmax(1), sa_.argmax(1)) == yte).mean()))
    print("seed", seed, "%.0fs" % (time.time() - t0), flush=True)
for k, v in R.items(): print("%-52s %.4f" % (k, np.mean(v)), flush=True)
