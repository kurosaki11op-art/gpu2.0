"""(60,000-image version, 22 Oct 2026: NPS images per stage, 10,000 test images, follow interval max(100, NPS/30)) A second look (20 Oct 2026) SIMULATED. Two counting tables learn in parallel: A on the shipped coarse code (5x5 patches, stride 2: 4,608 bits, about 263 active), B on the finer code (3x3 patches, stride 1, pooled 3x3: 8,192 bits, about 537 active). Decision rules:
  coarse   table A alone (shipped)
  fine     table B alone
  sum      scores of A and B added
  look     A answers when its top-2 margin is at least TH; otherwise the fine code is read and the scores of A and B are added (TH = the percentile LOOKP of A's margins on the training examples, so a known share of inputs gets the second look)
One pass and 5 stages, margin 256 / 1,500 dreams / 1 night, 3 seeds; reports accuracy and the mean active bits read per decision (reads of the first look plus, for second looks, the fine code).
usage: DATA_DIR"""
import os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
import feature_layer, detector_learn
from feature_layer import Features, patches, binarize
from cortex_core import load
from cortex_slow import CortexSlow
D = sys.argv[1]; STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; LOOKP = float(os.environ.get("LOOKP", 70)); t0 = time.time()


def learn_fine(x, F=32, chans=(50, 150, ("on", 8), ("off", 8)), nb=9, pool=3):
    out = []
    for c in chans:
        sd = detector_learn.StreamDetectors(F, nb=nb); pp, _ = patches(binarize(x, c)); sd.learn(pp); sd.reseed()
        f = Features(F, thr=c); f.cnt = sd.cnt.copy(); f.pool = pool; out.append(f)
    return out


NPS = int(os.environ.get("NPS", 12000)); SEEDS = int(os.environ.get("SEEDS", 2)); CHK = max(100, NPS // 30)
for DS in os.environ.get("DSS", "fashion,mnist").split(","):
    xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]; first = xtr[np.isin(ytr, STAGES[0])][:12000]
    enc = lambda fs, x: np.concatenate([np.concatenate([g.encode(x[i:i + 1000]) for g in fs], 1) for i in range(0, len(x), 1000)])
    fc = detector_learn.learn_features(first); ca_tr, ca_te = enc(fc, xtr), enc(fc, xte)
    feature_layer.PS, feature_layer.ST = 3, 1; ff = learn_fine(first); cb_tr, cb_te = enc(ff, xtr), enc(ff, xte); feature_layer.PS, feature_layer.ST = 5, 2
    reads_a, reads_b = float(ca_te.sum(1).mean()), float(cb_te.sum(1).mean()); R = {}
    for staged in (False, True):
        tag = "staged" if staged else "one pass"
        for seed in range(1, SEEDS + 1):
            def build(code):
                m = CortexSlow(code.shape[1], ch=CHK, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)
                for i, s in enumerate(STAGES if staged else [tuple(range(10))]):
                    o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]; m.stage(code[o], ytr[o])
                return m
            A, B = build(ca_tr), build(cb_tr)
            sc = lambda m, c: np.where(m.known[None, :], c.astype(np.int32) @ m.S.T.astype(np.int32), -(1 << 28))
            sa_tr = sc(A, ca_tr); srt = np.sort(sa_tr, 1); th = np.percentile(srt[:, -1] - srt[:, -2], LOOKP)
            sa, sb = sc(A, ca_te), sc(B, cb_te); sab = sa + sb; srt = np.sort(sa, 1); look = (srt[:, -1] - srt[:, -2]) < th
            for name, p in (("coarse", sa.argmax(1)), ("fine", sb.argmax(1)), ("sum of both", sab.argmax(1))):
                R.setdefault((name, tag), []).append(float((p == yte).mean()))
            mg_te = srt[:, -1] - srt[:, -2]                                                  # the share of second looks is set from the UNLABELLED margin distribution of the stream (no labels used)
            for share in (20, 40, 60, 80):
                lk = mg_te < np.percentile(mg_te, share); p = np.where(lk, sab.argmax(1), sa.argmax(1)); R.setdefault(("second look %d%%" % share, tag), []).append(float((p == yte).mean())); R.setdefault(("reads look %d%%" % share, tag), []).append(reads_a + lk.mean() * reads_b)
    for (name, tag), v in R.items():
        if not name.startswith("reads"): print(DS, "%-18s %-9s accuracy %.4f%s" % (name, tag, np.mean(v), ("   (mean active bits read %.0f)" % np.mean(R[("reads look " + name.split()[-1], tag)])) if name.startswith("second look") else ""), flush=True)
    print(DS, "active bits read per decision: coarse %.0f, fine %.0f, both %.0f" % (reads_a, reads_b, reads_a + reads_b), flush=True)
