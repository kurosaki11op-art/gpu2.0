"""Diagnosis of the old / new boundary for spoken words (20 Oct), answering: unequal treatment of old and new classes? overlapping features of the disputed pairs? learning-order vs word identity?
Aligned word codes (23,040 bits). Protocols (3 draws, single view, SIMULATED):
  A. SHIPPED: chip learns the old group (5 words, all recordings) then the new group from k recordings (IMPRINT + short sleep), k = 1, 5. Group membership OLD=0-4 or SWAP (old = 5-9).
  B. EQUAL: all ten words from scratch with the SAME k recordings each (no old/new difference in enrollment), chip table (IMPRINT) and a mean-prototype L1 nearest-prototype classifier (identical readout for every class).
Reported: accuracy per group, errors that cross the group boundary, and the most frequent confusions by word name. usage: DATA_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import cochlea
from cortex_int import CortexInt
D = sys.argv[1]; W = cochlea.WORDS
z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f = np.load(os.path.join(D, "speech_framesums_int.npz"))
y, te = f["y"], f["te"]; ytr, yte = y[~te].astype(int), y[te].astype(int); ctr, cte = z["tr"], z["te"]; cf = cte.astype(np.float32)


def report(name, conf, groupA):
    tot = conf.sum(1); acc = np.diag(conf).sum() / conf.sum()
    ga, gb = np.array(groupA), np.array([c for c in range(10) if c not in groupA])
    accA = np.diag(conf)[ga].sum() / conf[ga].sum(); accB = np.diag(conf)[gb].sum() / conf[gb].sum()
    cross_ab = conf[np.ix_(ga, gb)].sum() / conf[ga].sum(); cross_ba = conf[np.ix_(gb, ga)].sum() / conf[gb].sum()
    off = conf.copy().astype(float); np.fill_diagonal(off, 0); top = np.dstack(np.unravel_index(np.argsort(-off.ravel())[:5], off.shape))[0]
    print(f"{name}: all {acc:.3f} | group-A (first {len(ga)} listed) {accA:.3f}, group-B {accB:.3f} | A->B errors {cross_ab:.3f}, B->A errors {cross_ba:.3f} | top confusions " +
          ", ".join(f"{W[a]}->{W[b]} {off[a, b] / tot[a]:.2f}" for a, b in top), flush=True)


def proto_scores(codes, labels):
    p = np.stack([codes[labels == c].mean(0) for c in range(10)]).astype(np.float32)
    return cf @ (2 * p - 1).T - p.sum(1)[None, :]


for swap in (False, True):
    perm = np.arange(10)
    old = [0, 1, 2, 3, 4] if not swap else [5, 6, 7, 8, 9]; new = [c for c in range(10) if c not in old]
    for k in (1, 5):
        conf = np.zeros((10, 10), int)
        for s in (1, 2, 3):
            g = np.random.RandomState(1000 * s); so = np.where(np.isin(ytr, old))[0]; so = so[g.permutation(len(so))]
            sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in new]); sn = sn[g.permutation(len(sn))]
            m = CortexInt(ctr.shape[1], seed=s, imprint=4, B=10, night=2, daydream=1, night_stop=2); m.stage(ctr[so], ytr[so]); m.stage(ctr[sn], ytr[sn])
            p = (cte.astype(np.int32) @ m.W.T.astype(np.int32)).argmax(1)
            np.add.at(conf, (yte, p), 1)
        report(f"SHIPPED{'(swap)' if swap else ''} k={k} chip", conf, new)
for k in (1, 5, 20):
    conf_c = np.zeros((10, 10), int); conf_p = np.zeros((10, 10), int)
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s); idx = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(10)]); idx = idx[g.permutation(len(idx))]
        m = CortexInt(ctr.shape[1], seed=s, imprint=4, B=10, night=0, daydream=0); m.stage(ctr[idx], ytr[idx])
        np.add.at(conf_c, (yte, (cte.astype(np.int32) @ m.W.T.astype(np.int32)).argmax(1)), 1)
        np.add.at(conf_p, (yte, proto_scores(ctr[idx], ytr[idx]).argmax(1)), 1)
    report(f"EQUAL k={k} chip table ", conf_c, [5, 6, 7, 8, 9]); report(f"EQUAL k={k} prototype-L1", conf_p, [5, 6, 7, 8, 9])
