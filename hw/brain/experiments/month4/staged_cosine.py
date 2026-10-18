"""Class-incremental fixes from the GPU literature, multiplier-free, on STAGED clothing / digits (5 stages, today's chip, slow table off): decision-time score normalisation.
  cosine : score_c scaled by 2^-blen(L1 mass of row c) (a shift), like a cosine classifier / weight alignment with power-of-two gains
  mass_align : only the rows of OLD classes are rescaled so their mean mass equals the NEW classes' (weight aligning, WA)
  bias_dream : per-class bias = alpha * (mean score of class c's own dreams - global mean)   (already tested: +0.9)
2 seeds. SIMULATED. usage: DATA_DIR DS"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS); ctr, cte = z["tr"], z["te"].astype(np.int32); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; rows = {}
for seed in (1, 2):
    m = CortexInt(ctr.shape[1], night_stop=2, daydream=1, seed=seed)
    for i, s in enumerate(stages):
        sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; m.stage(ctr[sel], ytr[sel])
    W = m.W.astype(np.int64); sc = (cte @ m.W.T.astype(np.int32)).astype(np.int64); mass = np.abs(W).sum(1)
    bl = np.array([int(v).bit_length() for v in mass])
    var = {"plain": sc, "cosine": (sc << 14) >> bl[None, :]}
    # exact-ish cosine for reference (float): upper bound of this family
    var["cosine_float"] = sc / mass[None, :]
    old = np.arange(10) < 8; r = mass[~old].mean() / mass[old].mean()
    var["mass_align"] = np.where(old[None, :], sc * r, sc)
    for gamma in (0.25, 0.5, 0.75):
        var[f"mass^{gamma}"] = sc / (mass[None, :] ** gamma)
    for name, v in var.items():
        rows.setdefault(name, []).append(float((v.argmax(1) == yte).mean()))
for name, v in rows.items():
    print(f"{DS} {name:14s} {np.mean(v):.4f}", flush=True)
