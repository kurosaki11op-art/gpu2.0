"""27 Oct 2026, SIMULATED. MULTI-THRESHOLD TEST ON L ITSELF (not a stand-in). L's front end is one bank of 32 Hebbian detectors (5x5 patches, stride 1, OR-pooled over 4x4, 1,152 bits) per binary input channel; the shipped channels are pixel > 50, pixel > 150, centre-surround 'on' 8 and 'off' 8 (4 banks, 4,608 bits). The stand-in test showed that finer grey levels at the input help. Here more threshold banks are added to the real L front end, each fitted exactly as L fits its banks (unlabelled images, same recipe), and every combination is read by the same counting table (CortexSlow margin rule, integers only).
Each distinct channel is encoded once and cached. Reported per combination: bits, active bits per image, accuracy, cluster accuracy, Shirt recall, Shirt AP; reference is the shipped four channels (88.85)."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, ytr, xte, yte, train_table, CL, Features
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"; t0 = time.time(); cache = {}
def name(c): return "%s%d" % (c[0], c[1]) if isinstance(c, tuple) else "t%d" % c
def chan(c):
    if c in cache: return cache[c]
    f = SP + "chan_" + name(c) + ".npz"
    if os.path.exists(f): z = np.load(f); cache[c] = (z["a"], z["b"]); return cache[c]
    fe = Features(32, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000])
    enc = lambda x: np.concatenate([fe.encode(x[i:i + 5000]) for i in range(0, len(x), 5000)]).astype(np.uint8)
    a, b = enc(xtr), enc(xte); np.savez(f, a=a, b=b); cache[c] = (a, b); print("  encoded channel %-6s [%.0fs]" % (name(c), time.time() - t0), flush=True); return cache[c]
ON, OFF = ("on", 8), ("off", 8)
CONFIGS = [("shipped: 50,150,on8,off8", [50, 150, ON, OFF]), ("two thresholds only: 50,150", [50, 150]), ("four thresholds: 32,96,160,224", [32, 96, 160, 224]),
           ("five thresholds: 32,80,128,176,224", [32, 80, 128, 176, 224]), ("shipped + two thresholds: 50,100,150,200,on8,off8", [50, 100, 150, 200, ON, OFF]),
           ("five thresholds + on8 + off8", [32, 80, 128, 176, 224, ON, OFF]), ("eight thresholds: 16,48,...,240", [16, 48, 80, 112, 144, 176, 208, 240]), ("eight thresholds + on8 + off8", [16, 48, 80, 112, 144, 176, 208, 240, ON, OFF])]
for tag, chs in CONFIGS:
    A = np.concatenate([chan(c)[0] for c in chs], 1); B = np.concatenate([chan(c)[1] for c in chs], 1); W = train_table(A, ytr); S = B.astype(np.int32) @ W; p = S.argmax(1); mk = np.isin(yte, CL)
    s6 = S[:, 6] - np.delete(S, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
    print("RESULT %-52s %5d bits, %4.0f active: acc %.4f | cluster %.4f | Shirt recall %.3f | Shirt AP %.3f [%.0fs]" % (tag, A.shape[1], B.sum(1).mean(), (p == yte).mean(), (CL[S[mk][:, CL].argmax(1)] == yte[mk]).mean(), (p[yte == 6] == 6).mean(), ap, time.time() - t0), flush=True)
