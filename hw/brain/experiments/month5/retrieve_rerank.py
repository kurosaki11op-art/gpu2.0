"""25 Oct 2026, SIMULATED, EMNIST-balanced, one seed. Our own method 1: RETRIEVE, THEN RERANK (candidate generation with an inverted index, then exact scoring of a few classes).
Trained table: L's CortexSlow counting table on L's 4,608-bit code (K classes). Each class keeps a signature of its s most distinguishing bits (largest weight above the other classes' mean); the signatures form an inverted index (bit -> list of classes). Decision: stage 1, every active bit reads its short list and votes for those classes (votes = sum of the class's weight at that bit); the C classes with the most votes are candidates; stage 2, only those C classes are scored exactly (sum of their weights over the active bits) and the best wins. Adds and lookups only.
Cost counted in table entries read per decision: stage 1 = sum over active bits of (list length + 1 pointer); stage 2 = C x active bits; full table = active bits x K.
env: K, S (signature sizes), C (candidate counts)"""
import os, sys, time
import numpy as np
sys.path.insert(0, "/home/user/gpu2.0/hw/brain")
from cortex_slow import CortexSlow
E = lambda k, d: type(d)(os.environ.get(k, d))
K = E("K", 47); SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"
z = np.load(SP + "emnist_codes.npz"); ctr, ytr, cte, yte = z["ctr"], z["ytr"].astype(np.int64), z["cte"], z["yte"].astype(np.int64)
tr, te = ytr < K, yte < K; ctr, ytr, cte, yte = ctr[tr], ytr[tr], cte[te], yte[te]; NB = ctr.shape[1]
t0 = time.time(); m = CortexSlow(NB, n_cls=K, ch=500, K=5, night_stop=2, daydream=1, seed=1); o = np.random.RandomState(100).permutation(len(ytr)); m.stage(ctr[o], ytr[o]); W = m.S.T.astype(np.float32)        # (NB, K)
X = cte.astype(np.float32); act = X[:2000].sum(1).mean(); full = (X @ W).argmax(1); print("[%3.0fs] K=%d: full table accuracy %.4f, %.0f active bits, full reads %.0f entries; top-1 %.4f, top-2 %.4f, top-4 %.4f, top-8 %.4f" % (time.time() - t0, K, (full == yte).mean(), act, act * K, (full == yte).mean(), *[(np.argsort(-(X @ W), 1)[:, :k] == yte[:, None]).any(1).mean() for k in (2, 4, 8)]), flush=True)
excl = (W.sum(1, keepdims=True) - W) / (K - 1); dist = W - excl                                      # how much more class c weighs at bit b than the other classes on average
print("%-5s %-4s | %-8s %-9s | %-10s %-10s %-10s %-8s" % ("sig", "C", "acc", "recall@C", "stage1 rd", "stage2 rd", "total rd", "vs full"))
for S in [int(v) for v in E("SS", "20,50,100,200").split(",")]:
    sig = np.zeros((NB, K), np.float32)
    for c in range(K): top = np.argsort(-dist[:, c])[:S]; sig[top, c] = 1
    list_len = sig.sum(1); votes = X @ (sig * np.maximum(W, 0))                                          # stage 1 votes (lookups of the lists, adds of the class weights)
    st1 = (X[:2000] @ list_len).mean() + act
    for C in [int(v) for v in E("CC", "2,4,8").split(",")]:
        cand = np.argsort(-votes, 1)[:, :C]; recall = (cand == yte[:, None]).any(1).mean(); scores = X @ W; mask = np.full_like(scores, -1e9); np.put_along_axis(mask, cand, 0, axis=1); acc = ((scores + mask).argmax(1) == yte).mean()
        st2 = act * C; print("%-5d %-4d | %-8.4f %-9.4f | %-10.0f %-10.0f %-10.0f %-8.1f" % (S, C, acc, recall, st1, st2, st1 + st2, act * K / (st1 + st2)), flush=True)
