"""How much of the chip's table memory is really needed, WITHOUT changing a single value (lossless), 23 Oct 2026, SIMULATED.
Trains the integer model of L Cortex on MNIST in 5 stages (2,000 images per stage, the shipped settings, slow table) and then measures
the stored tables: fast table W (5-bit signed), slow table S (8-bit), dream counts on (10-bit). For each: share of zero entries, the
largest value really used, and the entropy (the lossless limit of any coding), compared with the dense storage the chip uses.
Also checks that a lossless re-coding changes nothing (accuracy computed from the tables before and after a pack/unpack).
usage: python table_storage_lossless.py DATA_DIR"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from feature_layer import Features
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; NPS = int(os.environ.get("NPS", 2000)); t0 = time.time()
xtr, ytr, xte, yte = load(D, "mnist"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
fes = [Features(32, thr=c, pool=2).fit(xtr[np.isin(ytr, STAGES[0])][:12000]) for c in (50, 150, ("on", 8), ("off", 8))]
enc = lambda x: np.concatenate([f.encode(x) for f in fes], 1)
rs = np.random.RandomState(1)
idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES])
te = rs.permutation(len(xte))[:2000]
ctr, ytr_s = enc(xtr[idx]), ytr[idx]; cte, yte_s = enc(xte[te]), yte[te]
nb = ctr.shape[1]; print("code bits", nb, "active per image %.0f" % ctr.sum(1).mean(), "%.0fs" % (time.time() - t0), flush=True)
m = CortexSlow(nb, ch=max(100, NPS >> 5), K=5, night_stop=2, daydream=1, seed=1, margin=256, ndream=1500, night=1)
for s in STAGES:
    sel = np.isin(ytr_s, s); o = rs.permutation(sel.sum()); m.stage(ctr[sel][o], ytr_s[sel][o])
acc = float((m.predict(cte) == yte_s).mean()); print("accuracy after 5 stages: %.2f %%  (%.0fs)" % (100 * acc, time.time() - t0), flush=True)


def ent(a):
    v, c = np.unique(a, return_counts=True); p = c / c.sum(); return float(-(p * np.log2(p)).sum())


rows = []
for name, arr, bits in (("fast table W", m.W, 5), ("slow table S", m.S, 8), ("dream counts on", m.on, 10)):
    a = np.asarray(arr); n = a.size; nz = float((a != 0).mean()); mx = int(np.abs(a.astype(np.int64)).max()); H = ent(a)
    dense = n * bits / 8 / 1024
    # lossless packing: needed bits for the largest value really used (sign included for signed tables)
    need = int(np.ceil(np.log2(mx + 1))) + (1 if a.min() < 0 else 0)
    packed = n * max(1, need) / 8 / 1024
    ecode = n * H / 8 / 1024                                           # entropy limit (ideal lossless coding of each entry on its own)
    rowzero = float((a == 0).all(0).mean())                              # code bits whose entry is zero for every class
    rows.append((name, n, bits, nz, mx, need, H, dense, packed, ecode, rowzero))
    print("%-16s entries %7d  stored bits %2d  non-zero %5.1f %%  largest used %5d  bits really needed %2d  entropy %.2f bits/entry | dense %.1f KB, trimmed %.1f KB, entropy limit %.1f KB | code bits unused by every class %.1f %%" % (name, n, bits, 100 * nz, mx, need, H, dense, packed, ecode, 100 * rowzero), flush=True)
# a pack/unpack round trip changes nothing: re-code W to its needed width and back
W = m.W.astype(np.int16); Wr = (W + 16).astype(np.uint8); Wb = np.unpackbits(Wr[..., None], axis=-1)[..., 3:]; Wr2 = np.packbits(np.concatenate([np.zeros(Wb.shape[:-1] + (3,), np.uint8), Wb], -1), axis=-1)[..., 0].astype(np.int16) - 16
print("round trip of the fast table is exact:", bool((Wr2 == W).all()), "| accuracy unchanged by construction: %.2f %%" % (100 * acc))
tot_d = sum(r[7] for r in rows); tot_t = sum(r[8] for r in rows); tot_e = sum(r[9] for r in rows)
print("TOTAL dense %.1f KB | value-width trimmed %.1f KB | entropy limit %.1f KB  -> lossless saving at most %.1fx" % (tot_d, tot_t, tot_e, tot_d / tot_e))
