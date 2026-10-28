"""28 Oct 2026, SIMULATED. COMPLEMENTARY DETECTORS (learned from the overlap failures: gains from more channels, two-level codes, clauses and smarter routers all re-read the same information). Selection so far ranked each detector by its own class information (mutual information) and kept the top 64 of a 128-detector pool; two detectors that say the same thing are both kept. Here the choice is greedy and redundancy-aware (counting only, learning time only): pick the detector with the highest class information minus lambda times its average redundancy with the detectors already picked (redundancy = mean over the 36 window positions of the correlation between the two detectors' pooled bits, from counts). The chip runs the chosen detectors alone (winner-take-all among them), exactly as in the deployable selection test.
Variants per channel (64 of 128, installed alone): (a) top information (the reference, 90.26 and 89.97 on two seeds), (b) redundancy-aware lambda 0.5, (c) lambda 1.0, (d) lambda 2.0, (e) random (control). All read by the same counting table.
env: SEED, LAMS."""
import os, sys, time, copy
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, ytr, xte, yte, train_table, CL, Features
E_ = lambda k, d: type(d)(os.environ.get(k, d)); SEED = E_("SEED", 0); LAMS = [float(v) for v in E_("LAMS", "0.5,1.0,2.0").split(",")]; POOLF = 128; KSEL = 64; K = 10; t0 = time.time()
CH = [50, 150, ("on", 8), ("off", 8)]
def mi_per_detector(codes, y, F):
    N = len(y); n1 = np.stack([codes[y == c].sum(0) for c in range(K)]).astype(np.float64); nc = np.bincount(y, minlength=K).astype(np.float64); n1t = n1.sum(0); mi = np.zeros(codes.shape[1])
    for c in range(K):
        for b in (0, 1):
            nb = (n1[c] if b else nc[c] - n1[c]); nbt = (n1t if b else N - n1t); pcb = (nb + 0.5) / (N + 1); mi += pcb * np.log(pcb / ((nc[c] / N) * ((nbt + 0.5) / (N + 1))))
    return mi.reshape(36, F).sum(0)
def redundancy(codes, F):                                                                           # (F, F): mean over the 36 positions of the correlation between detectors' pooled bits
    X = codes.reshape(len(codes), 36, F).astype(np.float32); R = np.zeros((F, F), np.float64)
    for p in range(36):
        x = X[:, p, :]; x = x - x.mean(0); sd = x.std(0) + 1e-6; x = x / sd; R += np.abs(x.T @ x / len(x))
    R /= 36; np.fill_diagonal(R, 0); return R
pools, mis, reds = [], [], []
for c in CH:
    fe = Features(POOLF, seed=SEED, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]); pools.append(fe); sub = xtr[:20000]
    a = np.concatenate([fe.encode(sub[i:i + 2000]) for i in range(0, len(sub), 2000)]).astype(np.uint8); mis.append(mi_per_detector(a, ytr[:20000], POOLF)); reds.append(redundancy(a, POOLF)); print("  channel %s: pool scored [%.0fs]" % (c, time.time() - t0), flush=True)
def greedy(mi, R, lam, k):
    chosen = [int(np.argmax(mi))]; mi_n = mi / mi.max()
    while len(chosen) < k:
        score = mi_n - lam * R[:, chosen].mean(1); score[chosen] = -1e9; chosen.append(int(np.argmax(score)))
    return np.sort(np.array(chosen))
def subset(fe, idx): f2 = copy.copy(fe); f2.cnt = fe.cnt[idx].copy(); f2.F = len(idx); return f2
def run(tag, idxs):
    fes = [subset(pools[ch], idxs[ch]) for ch in range(4)]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for i in range(0, len(x), 2000)]) for g in fes], 1).astype(np.uint8)
    A, B = enc(xtr), enc(xte); W = train_table(A, ytr); S = B.astype(np.int32) @ W; p = S.argmax(1); mk = np.isin(yte, CL); s6 = S[:, 6] - np.delete(S, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("RESULT %-44s %5d bits, %4.0f active: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f [%.0fs]" % (tag, A.shape[1], B.sum(1).mean(), (p == yte).mean(), (CL[S[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap, time.time() - t0), flush=True)
run("(a) top information (reference)", [np.sort(np.argsort(-mis[ch])[:KSEL]) for ch in range(4)])
for lam in LAMS: run("redundancy-aware, lambda %.1f" % lam, [greedy(mis[ch], reds[ch], lam, KSEL) for ch in range(4)])
rng = np.random.RandomState(0); run("random (control)", [np.sort(rng.permutation(POOLF)[:KSEL]) for ch in range(4)])
