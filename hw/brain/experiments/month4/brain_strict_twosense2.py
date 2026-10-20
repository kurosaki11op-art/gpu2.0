"""Cleaning the ear's names with the picture's own neighbours (20 Oct 2026) SIMULATED. Setup as brain_strict_twosense.py (ear trained on speakers 0-2, clips heard with the pictures from speakers 3-4); then, in sleep, pictures wait in a buffer of B; the K buffered pictures that overlap each picture most pool their class scores (from the table learned on the ear's noisy names) with its own, optionally plus a vote for the name the ear gave; the pooled winner becomes the label; a fresh table is learned on the cleaned names (1 or 2 rounds). Compare: names as given (noisy), cleaned, true labels.
Original header: Two senses (20 Oct 2026) SIMULATED. Vision = MNIST digits through the shipped retina code (4,608 bits); hearing = FSDD spoken digits (zero..nine, 6 speakers, 8 kHz) through the integer cochlea, noise floor, word alignment and the sound detector rule (10 channels, 23,040 bits). The two sets share only the digit class; a seen digit is paired with a heard clip of the same digit
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


def clean(m, code, names, KN, B, lam):
    S_ = m.S.astype(np.int64); out = names.copy(); pooled_all = np.zeros(len(code), np.int64)
    for j in range(0, len(code), B):
        c = code[j:j + B]; s = c.astype(np.int32) @ S_.T; s[:, ~m.known] = -(1 << 40); ov = c.astype(np.int32) @ c.T.astype(np.int32); np.fill_diagonal(ov, -1)
        nn = np.argsort(-ov, 1)[:, :KN]; z = np.where(m.known[None, :], s, 0); pooled = z + z[nn].sum(1)
        if lam: pooled[np.arange(len(c)), names[j:j + B]] += lam * (KN + 1)                         # the ear's own name counts as a vote
        pooled = np.where(m.known[None, :], pooled, -(1 << 50)); out[j:j + B] = pooled.argmax(1)
    return out


R = {}
for seed in range(1, SEEDS + 1):
    r = np.random.RandomState(seed); sp = spk[~stest]; ear2 = fit(atr[sp <= 2], satr[sp <= 2], seed); pool = np.where(sp >= 3)[0]
    pair2 = np.array([r.choice(pool[satr[pool] == d]) for d in ytr]); names = ear2.predict(atr[pair2]); R.setdefault("ear's names correct", []).append(float((names == ytr).mean()))
    R.setdefault("picture learner, ear's names as given", []).append(acc(fit(vtr, names, seed), vte, yte)); R.setdefault("picture learner, true labels (reference)", []).append(acc(fit(vtr, ytr, seed), vte, yte))
    for KN, B, lam, rounds in ((5, 128, 0, 1), (5, 128, 0, 2), (5, 128, 200, 1), (5, 128, 200, 2), (8, 256, 0, 2), (8, 256, 200, 2)):
        lab = names; m = fit(vtr, lab, seed)
        for rd in range(rounds): lab = clean(m, vtr, names if lam else lab, KN, B, lam); m = fit(vtr, lab, seed)
        key = "cleaned: K=%d buffer=%d ear vote=%s rounds=%d" % (KN, B, "yes" if lam else "no", rounds); R.setdefault(key, []).append(acc(m, vte, yte)); R.setdefault("  " + key + " | names correct", []).append(float((lab == ytr).mean()))
    print("seed", seed, "%.0fs" % (time.time() - t0), flush=True)
for k, v in R.items(): print("%-70s %.4f" % (k, np.mean(v)), flush=True)
