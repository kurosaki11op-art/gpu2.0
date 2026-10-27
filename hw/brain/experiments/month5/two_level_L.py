"""27 Oct 2026, SIMULATED. TWO-LEVEL OUTPUT CODE ON L ITSELF. L reports each detector per 4x4 pooled window as one bit: 'this detector won at some position inside the window' (OR-pooling). Two-level code: keep that bit and add a second bit 'this detector won at T or more of the 16 positions inside the window' (a count and a compare, no multiply). Same detectors as L (fitted exactly as shipped), same counting table.
Sanity check first: the 'at least one' bits recomputed here must equal L's cached code. Configurations: the shipped four channels and the seven-channel input of the multi-threshold test (five thresholds + on8 + off8), each as one-level (reference), two-level with T = 2, 3, 4, and three-level (1, 2, 4)."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, ytr, xte, yte, train_table, CL, Features
from feature_layer import patches, support_filter, binarize
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"; t0 = time.time()
ON, OFF = ("on", 8), ("off", 8)
def name(c): return "%s%d" % (c[0], c[1]) if isinstance(c, tuple) else "t%d" % c
def counts(fe, x):                                                                                    # (B, 6, 6, 32) number of positions in each 4x4 window where each detector won
    p, n = patches(support_filter(binarize(x, fe.thr), fe.support)); B = len(x); W = fe.winners(p.reshape(-1, p.shape[-1])).reshape(B, n, n); on = (p.sum(2) >= fe.min_on).reshape(B, n, n); m = n // fe.pool
    cnt = np.zeros((B, m, m, fe.F), np.uint8)
    for di in range(fe.pool):
        for dj in range(fe.pool):
            ww = W[:, di:m * fe.pool:fe.pool, dj:m * fe.pool:fe.pool]; oo = on[:, di:m * fe.pool:fe.pool, dj:m * fe.pool:fe.pool]; bi, ii, jj = np.nonzero(oo); cnt[bi, ii, jj, ww[bi, ii, jj]] += 1
    return cnt.reshape(B, -1)
cache = {}
def chan(c):
    if c in cache: return cache[c]
    f = SP + "cnt_" + name(c) + ".npz"
    if os.path.exists(f): z = np.load(f); cache[c] = (z["a"], z["b"]); return cache[c]
    fe = Features(32, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000])
    enc = lambda x: np.concatenate([counts(fe, x[i:i + 2000]) for i in range(0, len(x), 2000)])
    a, b = enc(xtr), enc(xte); np.savez(f, a=a, b=b); cache[c] = (a, b); print("  counted channel %-6s [%.0fs]" % (name(c), time.time() - t0), flush=True); return cache[c]
ch_ship = [50, 150, ON, OFF]; ch_seven = [32, 80, 128, 176, 224, ON, OFF]
z = np.load(SP + "shirt_cache.npz"); ok = all((chan(c)[0] >= 1).astype(np.uint8).tolist() == z["ctr"][:, i * 1152:(i + 1) * 1152].tolist() for i, c in enumerate(ch_ship[:1])) if False else None
a0 = np.concatenate([(chan(c)[0] >= 1) for c in ch_ship], 1).astype(np.uint8); print("sanity: recomputed one-level code equals L's cached code: %s" % bool((a0 == z["ctr"]).all()), flush=True)
def code(chs, levels, which):                                                                         # which: 0 train, 1 test
    return np.concatenate([np.concatenate([(chan(c)[which] >= t) for t in levels], 1) for c in chs], 1).astype(np.uint8)
def run(tag, chs, levels):
    A, B = code(chs, levels, 0), code(chs, levels, 1); W = train_table(A, ytr); S = B.astype(np.int32) @ W; p = S.argmax(1); mk = np.isin(yte, CL); s6 = S[:, 6] - np.delete(S, 6, 1).max(1); yy = yte == 6
    o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("RESULT %-44s %5d bits, %4.0f active: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f [%.0fs]" % (tag, A.shape[1], B.sum(1).mean(), (p == yte).mean(), (CL[S[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap, time.time() - t0), flush=True)
for T in ((1,), (1, 2), (1, 3), (1, 4), (1, 2, 4)): run("shipped 4 channels, levels %s" % (T,), ch_ship, T)
for T in ((1,), (1, 2), (1, 3), (1, 2, 4)): run("seven channels, levels %s" % (T,), ch_seven, T)
