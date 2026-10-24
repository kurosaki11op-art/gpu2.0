"""Knockout screen of the detectors (24 Oct 2026, SIMULATED, Fashion-MNIST, single view, one seed). Gene-editing analogy: find the faulty 'genes' before repairing anything.
Table trained on 30,000 training images with the shipped detectors (32 per channel x 4 channels = 128). For each detector the bits it produces are switched off (masked) and the held-out score is re-measured with the table AS IT IS (no retraining): essential (removal hurts), neutral, or faulty (removal helps).
Verdicts are made on check set A (10,000 other training images) and CONFIRMED on check set B (10,000 further training images); the test set (10,000) is touched only for the final drop/keep comparison.
Score used: accuracy + Shirt average precision (both must not fall for a detector to be called neutral)."""
import sys, os, time, numpy as np
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features
from cortex_core import load
from cortex_slow import CortexSlow
D, DS = sys.argv[1], sys.argv[2]; xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); CL = np.array([0, 2, 4, 6]); t0 = time.time()
NTR = 30000; iA = np.arange(NTR, NTR + 10000); iB = np.arange(NTR + 10000, NTR + 20000); CH = (50, 150, ("on", 8), ("off", 8)); F = 32
rs = np.random.RandomState(7); fes = [Features(F, thr=c, pool=4).fit(xtr[:NTR][rs.choice(NTR, 12000, replace=False)]) for c in CH]
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 200]) for g in fes], 1) for i in range(0, len(x), 200)])
ctr, cA, cB, cT = enc(xtr[:NTR]), enc(xtr[iA]), enc(xtr[iB]), enc(xte); print("codes %d bits, encoded in %.0fs" % (ctr.shape[1], time.time() - t0), flush=True)
m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); sel = np.random.RandomState(100).permutation(NTR); m.stage(ctr[sel], ytr[:NTR][sel]); S = m.S.astype(np.int32)
def score(code, y, mask=None):
    c = code.astype(np.int32); sc = c @ S.T if mask is None else (c * mask) @ S.T; p = sc.argmax(1); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = y == 6; o = np.argsort(-s); tp = np.cumsum(yy[o])
    return (p == y).mean(), ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
m_ch = ctr.shape[1] // len(CH); cells = m_ch // F
def bits_of(ch, k): return ch * m_ch + np.arange(cells) * F + k                      # all bits (every cell) of detector k in channel ch
baseA, baseB = score(cA, ytr[iA]), score(cB, ytr[iB]); print("base: check A acc %.4f AP %.3f | check B acc %.4f AP %.3f" % (*baseA, *baseB), flush=True)
rows = []
for ch in range(len(CH)):
    for k in range(F):
        mask = np.ones(ctr.shape[1], np.int32); mask[bits_of(ch, k)] = 0
        a = score(cA, ytr[iA], mask); b = score(cB, ytr[iB], mask); rows.append((ch, k, a[0] - baseA[0], a[1] - baseA[1], b[0] - baseB[0], b[1] - baseB[1], cA[:, bits_of(ch, k)].sum(1).mean()))
R = np.array(rows); dA = R[:, 2]; dB = R[:, 4]; apA = R[:, 3]; apB = R[:, 5]
print("correlation of the removal effect on accuracy between check A and check B: %.2f; on Shirt AP: %.2f (1 = the screen is stable)" % (np.corrcoef(dA, dB)[0, 1], np.corrcoef(apA, apB)[0, 1]), flush=True)
ess = (dA < -0.0015); faulty = (dA > 0.0005) & (apA > -0.002); neutral = ~ess & ~faulty
print("verdict on check A: essential %d, neutral %d, faulty %d (of %d)" % (ess.sum(), neutral.sum(), faulty.sum(), len(R)))
print("confirmed on check B: faulty detectors with removal effect > 0 on B too: %d of %d; essential with effect < 0 on B: %d of %d" % (((dB > 0) & faulty).sum(), faulty.sum(), ((dB < 0) & ess).sum(), ess.sum()), flush=True)
print("mean removal effect on B: faulty %+.4f, neutral %+.4f, essential %+.4f" % (dB[faulty].mean() if faulty.any() else 0, dB[neutral].mean() if neutral.any() else 0, dB[ess].mean() if ess.any() else 0))
def drop(which, tag):
    mask = np.ones(ctr.shape[1], np.int32)
    for i in np.where(which)[0]: mask[bits_of(int(R[i, 0]), int(R[i, 1]))] = 0
    keep = mask.astype(bool); m2 = CortexSlow(int(keep.sum()), ch=500, K=5, night_stop=2, daydream=1, seed=1); m2.stage(ctr[sel][:, keep], ytr[:NTR][sel]); S2 = m2.S.astype(np.int32)
    out = []
    for code, y in ((cB, ytr[iB]), (cT, yte)):
        sc = code[:, keep].astype(np.int32) @ S2.T; p = sc.argmax(1); s = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = y == 6; o = np.argsort(-s); tp = np.cumsum(yy[o]); out += [(p == y).mean(), ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()]
    print("%-44s bits %5d | check B acc %.4f AP %.3f | TEST acc %.4f Shirt AP %.3f" % (tag, int(keep.sum()), *out), flush=True)
drop(np.zeros(len(R), bool), "keep all (retrained)"); drop(faulty, "drop faulty (retrained)"); drop(faulty | (neutral & (dA > -0.0003)), "drop faulty + near-neutral (retrained)")
np.savez("knockout_result.npz", R=R)
