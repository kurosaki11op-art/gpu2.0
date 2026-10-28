"""28 Oct 2026, SIMULATED accuracy, ESTIMATED energy. THREE-STAGE CASCADE (founder's decision: matrix-free by default, multiplication where it pays, light-weight). Stage 1: L as shipped (matrix-free) on every image. Stage 2: the matrix-free 64-informative front end (installed alone, seed SEED) on the share r1 of images with the smallest stage-1 margin. Stage 3: the small int8 CNN (32 shared 3x3 filters, SIMULATED reference trained here, int8 weights, float activations) on the fraction f of stage-2 images with the smallest stage-2 margin (overall share r1 x f); its answer replaces the earlier ones.
Cost (ESTIMATED, cost_frontier.py model): stage-1 energy for every image + r1 x stage-2 energy + r1 x f x CNN energy (260 nJ at int8). Compared with: stage 1 + stage 2 only (90.35 at 40.6 nJ), stage 1 + CNN only (91.28 at 81.9 nJ for 20%)."""
import os, sys, time, copy
os.environ["ONLY"] = "none"; os.environ["F"] = "32"
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
import foundations_raw as R
from shirt_new_methods_setup import xtr, ytr, xte, yte, train_table, CL, Features, ctr, cte
E_ = lambda k, d: type(d)(os.environ.get(k, d)); SEED = E_("SEED", 0); POOLF = 128; KSEL = 64; K = 10; t0 = time.time()
def sram(kb): return 10.0 if kb <= 8 else 20.0 if kb <= 32 else 20.0 + 80.0 * min(1.0, (kb - 32) / 992)
fe_det = 576 * 0.23 / 1000; tab = lambda bits, act: act * (sram(bits * 10 / 1024) + 1.0) / 1000; E1 = 4 * 32 * fe_det + tab(4608, 589)
E_cnn = (248768 * 0.23 + (9 * 32 + 169 * 32 * 10) / 8 * sram((9 * 32 + 169 * 32 * 10) / 1024) + 26 * 26 * 32 / 8 * 2 * 10 + 980) / 1000
CH = [50, 150, ("on", 8), ("off", 8)]
def mi_per_detector(codes, y, F):
    N = len(y); n1 = np.stack([codes[y == c].sum(0) for c in range(K)]).astype(np.float64); nc = np.bincount(y, minlength=K).astype(np.float64); n1t = n1.sum(0); mi = np.zeros(codes.shape[1])
    for c in range(K):
        for b in (0, 1):
            nb = (n1[c] if b else nc[c] - n1[c]); nbt = (n1t if b else N - n1t); pcb = (nb + 0.5) / (N + 1); mi += pcb * np.log(pcb / ((nc[c] / N) * ((nbt + 0.5) / (N + 1))))
    return mi.reshape(36, F).sum(0)
fes = []
for c in CH:
    fe = Features(POOLF, seed=SEED, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]); sub = xtr[:20000]
    a = np.concatenate([fe.encode(sub[i:i + 2000]) for i in range(0, len(sub), 2000)]).astype(np.uint8); idx = np.sort(np.argsort(-mi_per_detector(a, ytr[:20000], POOLF))[:KSEL])
    f2 = copy.copy(fe); f2.cnt = fe.cnt[idx].copy(); f2.F = len(idx); fes.append(f2)
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for i in range(0, len(x), 2000)]) for g in fes], 1).astype(np.uint8)
A, B = enc(xtr), enc(xte); act = B.sum(1).mean(); E2 = 4 * KSEL * fe_det + tab(A.shape[1], act); print("stage-2 code encoded [%.0fs]" % (time.time() - t0), flush=True)
S0 = cte.astype(np.int32) @ train_table(ctr, ytr); S1 = B.astype(np.int32) @ train_table(A, ytr)
rs = np.random.RandomState(0); m = R.Model("cnn", False, F=32)
for e in range(20):
    order = rs.permutation(len(R.Xtr))
    for i in range(0, len(order), R.BS): j = order[i:i + R.BS]; m.step(R.Xtr[j], ytr[j])
q8 = lambda W: np.round(W / (np.abs(W).max() + 1e-12) * 127) / 127 * (np.abs(W).max() + 1e-12); m.Wc, m.W = q8(m.Wc), q8(m.W)
pc = np.concatenate([m.forward(R.Xte[i:i + 1000])[0].argmax(1) for i in range(0, len(R.Xte), 1000)]); print("CNN int8 trained [%.0fs]: alone acc %.4f" % (time.time() - t0, (pc == yte).mean()), flush=True)
zs = lambda S: (S - S.mean(1, keepdims=True)) / (S.std() + 1e-9)
def mg(S): s = np.sort(S, 1); return s[:, -1] - s[:, -2]
def metrics(p): mk = np.isin(yte, CL); return (p == yte).mean(), (p[yte == 6] == 6).mean(), (p[mk] == yte[mk]).mean()
m0 = mg(S0); p0 = S0.argmax(1); p1 = np.where(m0 <= np.quantile(m0, 1.0), p0, p0)
print("stage 1 alone: acc %.4f | Shirt recall %.3f | cluster %.4f | est. %.1f nJ" % (metrics(p0) + (E1,)), flush=True); print("CNN energy est. %.0f nJ, stage-2 energy est. %.1f nJ" % (E_cnn, E2), flush=True)
for r1 in (0.2, 0.3):
    route1 = m0 <= np.quantile(m0, r1); S = np.where(route1[:, None], zs(S1), zs(S0)); p = S.argmax(1); mm = mg(S1)
    print("RESULT stages 1+2, r1 %.0f%%:                       acc %.4f | Shirt recall %.3f | cluster %.4f | est. %.1f nJ (%.2f x L)" % ((100 * r1,) + metrics(p) + (E1 + r1 * E2, (E1 + r1 * E2) / E1)), flush=True)
    for f in (0.1, 0.25, 0.5):
        thr = np.quantile(mm[route1], f); route2 = route1 & (mm <= thr); pf = np.where(route2, pc, p); cost = E1 + r1 * E2 + route2.mean() * E_cnn
        print("RESULT stages 1+2+3, r1 %.0f%%, CNN on %2.0f%% of those (%.1f%% overall): acc %.4f | Shirt recall %.3f | cluster %.4f | est. %.1f nJ (%.2f x L)" % ((100 * r1, 100 * f, 100 * route2.mean()) + metrics(pf) + (cost, cost / E1)), flush=True)
for q in (0.05, 0.1, 0.2):
    route = m0 <= np.quantile(m0, q); pf = np.where(route, pc, p0); cost = E1 + q * E_cnn
    print("RESULT stages 1+3 only, CNN on %.0f%% of images:                acc %.4f | Shirt recall %.3f | cluster %.4f | est. %.1f nJ (%.2f x L)" % ((100 * q,) + metrics(pf) + (cost, cost / E1)), flush=True)
