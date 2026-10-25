"""25 Oct 2026, SIMULATED, Fashion-MNIST. L-Deep v2: weight-shared gate trees chosen by COUNTED INFORMATION instead of error passing (error passing through shared trees destabilised the layers above, see bool_conv.py).
Step 1 (STEP=1): generate R random trees (each: 4 leaf gates reading 8 random bits of a 5x5 window of the two threshold planes, 2 middle gates, 1 root gate, random truth tables), slide each over all 24x24 positions, OR-pool over 4x4 blocks (36 bits per tree), score every tree by the mutual information between its pooled bits and the class (counts on NSEL images), keep the best F. Saved.
Step 2 (STEP=2): encode NTR training and the test images with the selected trees and read them with L's counting table (CortexSlow); also together with L's own 4,608-bit code.
Everything is lookups, ORs and counts; no gradient, no multiply-accumulate.
env: STEP, R, F, NSEL, NTR"""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import xtr, xte, ytr, yte, ctr, cte, train_table, report
E = lambda k, d: type(d)(os.environ.get(k, d))
STEP, R, F, NSEL, NTR, SEED, DENS = E("STEP", 1), E("R", 256), E("F", 64), E("NSEL", 3000), E("NTR", 20000), E("SEED", 0), E("DENS", 1.0)
rs = np.random.RandomState(SEED); NP = 576; t0 = time.time()
TT = np.array([[[(g >> (2 * a + b)) & 1 for b in (0, 1)] for a in (0, 1)] for g in range(16)], np.int8)
SAVE = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/conv_select.npz"
def bits(x): im = x.reshape(-1, 28, 28); return np.stack([im > 85, im > 170], 1).astype(np.int8)
def windows(P):
    n = len(P); out = np.zeros((n, 24, 24, 2, 5, 5), np.int8)
    for dy in range(5):
        for dx in range(5): out[:, :, :, :, dy, dx] = P[:, :, dy:dy + 24, dx:dx + 24].transpose(0, 2, 3, 1)
    return out.reshape(n, NP, 50)
def run_trees(win, g, LA):
    """win (B,576,50); g (T,7) gate ids; LA (T,4,2) window bit indices -> pooled (B, T, 36) bits"""
    wa = win[:, :, LA[:, :, 0]]; wb = win[:, :, LA[:, :, 1]]                                   # (B,576,T,4)
    leaf = TT[g[None, None, :, :4], wa, wb]
    m0 = TT[g[None, None, :, 4], leaf[..., 0], leaf[..., 1]]; m1 = TT[g[None, None, :, 5], leaf[..., 2], leaf[..., 3]]
    root = TT[g[None, None, :, 6], m0, m1]                                                       # (B,576,T)
    return root.reshape(len(win), 6, 4, 6, 4, -1).max(axis=(2, 4)).reshape(len(win), 36, -1).transpose(0, 2, 1)
def encode(P, g, LA, chunk=100):
    return np.concatenate([run_trees(windows(P[i:i + chunk]), g, LA).reshape(min(chunk, len(P) - i), -1) for i in range(0, len(P), chunk)]).astype(np.uint8)
if STEP == 1:
    g = rs.randint(0, 16, (R, 7)); LA = np.stack([np.stack([rs.choice(50, 8, replace=False).reshape(4, 2) for _ in range(1)])[0] for _ in range(R)])
    P = bits(xtr[:NSEL]); y = ytr[:NSEL]; feats = np.concatenate([run_trees(windows(P[i:i + 50]), g, LA) for i in range(0, NSEL, 50)])          # (NSEL, R, 36)
    print("[%4.0fs] %d random trees applied to %d images" % (time.time() - t0, R, NSEL), flush=True)
    p = feats.mean(0) + 1e-6; mi = np.zeros((R, 36))
    for c in range(10):
        pc = feats[y == c].mean(0) + 1e-6; w = (y == c).mean()
        mi += w * (pc * np.log(pc / p) + (1 - pc) * np.log((1 - pc + 1e-6) / (1 - p + 1e-6)))
    score = mi.sum(1); onr = feats.mean((0, 2)); score = np.where(onr < DENS, score, -np.inf); print('trees under the density limit %.2f: %d of %d' % (DENS, int((onr < DENS).sum()), R)); keep = np.argsort(-score)[:F]
    print("tree information (nats summed over 36 pooled positions): best %.3f, median %.3f, selected worst %.3f; bits on: selected %.3f, all %.3f" % (score.max(), np.median(score), score[keep].min(), feats[:, keep].mean(), feats.mean()), flush=True)
    np.savez(SAVE, g=g[keep], LA=LA[keep], score=score[keep]); print("saved %d selected trees" % F)
else:
    z = np.load(SAVE); g, LA = z["g"], z["LA"]; Ptr = bits(xtr[:NTR]); Pte = bits(xte)
    ftr = encode(Ptr, g, LA); print("[%4.0fs] encoded %d training images: %d bits, %.0f on" % (time.time() - t0, NTR, ftr.shape[1], ftr.sum(1).mean()), flush=True)
    fte = encode(Pte, g, LA); print("[%4.0fs] encoded test" % (time.time() - t0), flush=True)
    W = train_table(ftr, ytr[:NTR]); report("L-Deep v2 features alone (%d selected trees) -> counting table" % len(g), fte.astype(np.int32) @ W)
    W = train_table(np.concatenate([ctr[:NTR], ftr], 1), ytr[:NTR]); report("L's code + L-Deep v2 features -> counting table", np.concatenate([cte, fte], 1).astype(np.int32) @ W)
    W = train_table(ctr[:NTR], ytr[:NTR]); report("reference: L's code alone (same %d training images)" % NTR, cte.astype(np.int32) @ W)
