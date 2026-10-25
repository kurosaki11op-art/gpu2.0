"""25 Oct 2026, SIMULATED, Omniglot (1,623 character classes, 20 drawings each, 28x28), one seed. Scaling test of RETRIEVE-THEN-RERANK at a large number of classes, with memory reads counted in 64-bit WORDS (not entries): a table row of K 6-bit entries needs ceil(6K/64) words; a list entry (class index + 6-bit weight) is ceil(log2 K)+6 bits.
STEP=1: decode, invert (strokes bright), split 12 train / 8 test drawings per class, fit L's detectors on 12,000 unlabelled images, encode (L's 4,608-bit code), cache.
STEP=2: train L's counting table (CortexSlow) on the 12 drawings per class (K classes), full-table accuracy and top-k recall; retrieve-then-rerank sweep over signature size S and candidates C; words read per decision against the full table.
env: STEP, K (number of classes used, default all 1,623), SS, CC"""
import os, sys, io, time
import numpy as np
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1
from feature_layer import Features
from cortex_slow import CortexSlow
E = lambda k, d: type(d)(os.environ.get(k, d))
STEP, K = E("STEP", 1), E("K", 1623); SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"; t0 = time.time()
if STEP == 1:
    import pyarrow.parquet as pq
    from PIL import Image
    t = pq.read_table("/tmp/omni/data/full-00000-of-00001-150a89c59f7b9041.parquet"); imgs = t.column("image").to_pylist(); lab = np.array(t.column("label").to_pylist())
    X = np.stack([np.array(Image.open(io.BytesIO(d["bytes"])).convert("L")) for d in imgs]).reshape(len(imgs), 784); X = 255 - X
    print("Omniglot: %d images, %d classes, %.0f gray mean after inversion" % (len(X), len(set(lab.tolist())), X.mean()), flush=True)
    rs = np.random.RandomState(0); tr = []; te = []
    for c in sorted(set(lab.tolist())):
        ix = np.where(lab == c)[0]; ix = rs.permutation(ix); tr += list(ix[:12]); te += list(ix[12:20])
    tr, te = np.array(tr), np.array(te); fes = [Features(32, thr=c, pool=4).fit(X[rs.permutation(len(X))[:12000]]) for c in (50, 150, ("on", 8), ("off", 8))]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)]).astype(np.uint8)
    ctr, cte = enc(X[tr]), enc(X[te]); print("[%4.0fs] encoded: %d train, %d test, %.0f active bits" % (time.time() - t0, len(tr), len(te), ctr.sum(1).mean()), flush=True)
    np.savez(SP + "omni_codes.npz", ctr=ctr, ytr=lab[tr], cte=cte, yte=lab[te])
else:
    z = np.load(SP + "omni_codes.npz"); ctr, ytr, cte, yte = z["ctr"], z["ytr"].astype(np.int64), z["cte"], z["yte"].astype(np.int64)
    keep = np.unique(ytr)[:K]; remap = {c: i for i, c in enumerate(keep)}; tr = np.isin(ytr, keep); te = np.isin(yte, keep); ctr, cte = ctr[tr], cte[te]; ytr = np.array([remap[c] for c in ytr[tr]]); yte = np.array([remap[c] for c in yte[te]]); NB = ctr.shape[1]
    m = CortexSlow(NB, n_cls=K, ch=500, K=5, night_stop=2, daydream=1, seed=1); o = np.random.RandomState(100).permutation(len(ytr)); m.stage(ctr[o], ytr[o]); W = m.S.T.astype(np.float32); print("[%4.0fs] table trained: K=%d, %d train images" % (time.time() - t0, K, len(ytr)), flush=True)
    X = cte.astype(np.float32); act = X[:2000].sum(1).mean(); scores = X @ W; full = scores.argmax(1)
    rec = lambda k: (np.argsort(-scores, 1)[:, :k] == yte[:, None]).any(1).mean()
    ib = int(np.ceil(np.log2(K))); words_row = int(np.ceil(6 * K / 64)); full_words = act * words_row
    print("full table: accuracy %.4f, top-4 %.4f, top-16 %.4f; %.0f active bits x %d words per row = %.0f words read per decision; table %.1f MB at 6 bits" % ((full == yte).mean(), rec(4), rec(16), act, words_row, full_words, NB * K * 6 / 8 / 1e6), flush=True)
    excl = (W.sum(1, keepdims=True) - W) / (K - 1); dist = W - excl
    print("%-5s %-4s | %-8s %-9s | %-12s %-12s %-12s %-8s" % ("sig", "C", "acc", "recall@C", "stage1 words", "stage2 words", "total words", "vs full"))
    for S in [int(v) for v in E("SS", "50,100,200").split(",")]:
        sig = np.zeros((NB, K), np.float32)
        for c in range(K): top = np.argpartition(-dist[:, c], S)[:S]; sig[top, c] = 1
        list_len = sig.sum(1); votes = X @ (sig * np.maximum(W, 0)); st1 = act * 1 + (X[:2000] @ np.ceil(list_len * (ib + 6) / 64)).mean()
        for C in [int(v) for v in E("CC", "8,16,32").split(",")]:
            cand = np.argsort(-votes, 1)[:, :C]; recall = (cand == yte[:, None]).any(1).mean(); sc = scores.copy(); mask = np.full_like(sc, -1e9); np.put_along_axis(mask, cand, 0, axis=1); acc = ((sc + mask).argmax(1) == yte).mean(); st2 = act * C
            print("%-5d %-4d | %-8.4f %-9.4f | %-12.0f %-12.0f %-12.0f %-8.1f" % (S, C, acc, recall, st1, st2, st1 + st2, full_words / (st1 + st2)), flush=True)
