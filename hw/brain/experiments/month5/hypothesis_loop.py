"""26 Oct 2026, SIMULATED. PART 3 of the research plan: the HYPOTHESIS LOOP (research note 3, Design A) on L's own counting table, Fashion-MNIST, one seed.
Observe: Shirt (6) is confused with T-shirt (0), Pullover (2), Coat (4). Propose: for each such pair, a contrast counter finds literals (bit on or off, over L's 4,608 detector bits + 1,568 raw pixel bits) that are common in Shirt and rare in the other class, and greedily conjoins 2 to 4 of them (Popper-style: a clause that fires on the wrong class is too general, so literals are only added). Test: each candidate is scored on a HELD set B (20,000 train images not used to propose it) with a Wilson lower bound: accepted only if lower bound of its firing rate on the target class minus upper bound on the other class exceeds MARGIN, it covers at least MINCOV of the target class, and fires on at most DAMAGE of all other classes (damage budget). Keep: the accepted clauses are added as bits to the table input; the whole batch is kept only if, on B, Shirt recall rises by at least GAIN and overall accuracy falls by at most 0.2 points; otherwise the batch is undone and halved (undo log printed). Control: random clauses with the same number of literals and the same coverage on Shirt pass through the same loop. Final: table retrained on all 60,000 images with the kept clauses; test accuracy, Shirt recall, cluster accuracy, Shirt AP, against L alone.
env: NCAND per pair, MARGIN, MINCOV, DAMAGE, GAIN."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.argv = ["x"]
from shirt_new_methods_setup import ctr, cte, ytr, yte, xtr, xte, train_table, CL
E_ = lambda k, d: type(d)(os.environ.get(k, d)); NCAND = E_("NCAND", 60); MARGIN = E_("MARGIN", 0.05); MINCOV = E_("MINCOV", 0.03); DAMAGE = E_("DAMAGE", 0.12); GAIN = E_("GAIN", 0.01)
def bits(x): im = x.reshape(-1, 28, 28); return np.concatenate([(im > 85).reshape(len(im), -1), (im > 170).reshape(len(im), -1)], 1).astype(np.uint8)
Z = np.concatenate([ctr, bits(xtr)], 1).astype(np.uint8); Zt = np.concatenate([cte, bits(xte)], 1).astype(np.uint8); NB = Z.shape[1]; t0 = time.time()
ia, ib = np.arange(40000), np.arange(40000, 60000); rs = np.random.RandomState(7)
def lits(M): return np.concatenate([M, 1 - M], 1)
def wilson(k, n, z=1.96):
    if n == 0: return 0.0, 1.0
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return c - h, c + h
def fire(M, lit_ids): 
    out = np.ones(len(M), bool)
    for l in lit_ids: out &= (M[:, l] == 1) if l < NB else (M[:, l - NB] == 0)
    return out
def propose(c, n, rng, maxlen=4, count=None):                                                                    # contrast counting on set A: grow a conjunction that fires on class c and not on class n
    Ac, An = Z[ia][ytr[ia] == c], Z[ia][ytr[ia] == n]; out = []
    for _ in range(count or NCAND):
        pc, pn = lits(Ac).mean(0), lits(An).mean(0); score = pc - pn; ok = pc >= 0.3; cand = np.where(ok)[0]
        if len(cand) == 0: break
        top = cand[np.argsort(-score[cand])[:40]]; first = rng.choice(top); chosen = [first]; mc = fire(Ac, chosen); mn = fire(An, chosen)
        while len(chosen) < maxlen and mn.sum() > 0.05 * len(An):
            pc2, pn2 = lits(Ac[mc]).mean(0), lits(An[mn]).mean(0) if mn.sum() else np.zeros(2 * NB); sc2 = (mc.mean() * pc2) - (mn.mean() * pn2); sc2[chosen] = -9; sc2[(pc2 < 0.5)] = -9
            if sc2.max() <= 0: break
            nxt = int(np.argmax(sc2 + 0.02 * rng.randn(len(sc2)))); chosen.append(nxt); mc = mc & fire(Ac, [nxt]) if False else fire(Ac, chosen); mn = fire(An, chosen)
        out.append(chosen)
    return out
def accept(cl, c, n):                                                                              # the held-set test with a damage budget
    B = Z[ib]; yb = ytr[ib]; f = fire(B, cl); fc = f[yb == c]; fn = f[yb == n]; lo_c, _ = wilson(fc.sum(), len(fc)); _, hi_n = wilson(fn.sum(), len(fn)); other = f[(yb != c) & (yb != n)].mean()
    return (lo_c - hi_n > MARGIN) and fc.mean() >= MINCOV and other <= DAMAGE, lo_c - hi_n
def table_eval(extra_tr, extra_te, idx_tr, idx_ev, Zev=None, y_ev=None, test=False):
    A = np.concatenate([ctr[idx_tr]] + ([extra_tr[idx_tr]] if extra_tr is not None else []), 1); W = train_table(A, ytr[idx_tr])
    Xe = (cte if test else ctr[idx_ev]); Xe = np.concatenate([Xe] + ([extra_te if test else extra_tr[idx_ev]] if extra_tr is not None else []), 1); sc = Xe.astype(np.int32) @ W; ye = yte if test else ytr[idx_ev]; p = sc.argmax(1)
    s6 = sc[:, 6] - np.delete(sc, 6, 1).max(1); yy = ye == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum(); mk = np.isin(ye, CL)
    return (p == ye).mean(), (p[ye == 6] == 6).mean(), (CL[sc[mk][:, CL].argmax(1)] == ye[mk]).mean(), ap
base_B = table_eval(None, None, ia, ib); print("[%4.0fs] L alone, trained on A, scored on held B: acc %.4f | Shirt recall %.3f | cluster %.4f | AP %.3f" % ((time.time() - t0,) + base_B), flush=True)
def run(kind):
    rng = np.random.RandomState(11 if kind == "hypothesis" else 12); cands = []
    for n in (0, 2, 4):
        if kind == "hypothesis": props = propose(6, n, rng)
        else:                                                                                            # random control: same lengths, same coverage on Shirt, literals chosen at random among bits that are common in Shirt
            A6 = Z[ia][ytr[ia] == 6]; common = np.where(lits(A6).mean(0) >= 0.3)[0]; props = []
            for _ in range(NCAND):
                for _t in range(30):
                    cl = list(rng.choice(common, rng.randint(2, 5), replace=False))
                    if fire(A6, cl).mean() >= MINCOV: props.append(cl); break
        for cl in props: cands.append((cl, n))
    print("  %s: %d candidates proposed" % (kind, len(cands)), flush=True)
    acc = []
    for cl, n in cands:
        ok, sc = accept(cl, 6, n)
        if ok: acc.append((sc, cl))
    acc.sort(key=lambda t: -t[0]); print("  %s: %d pass the held-set test (damage <= %.2f, lower-bound margin > %.2f)" % (kind, len(acc), DAMAGE, MARGIN), flush=True)
    keep = [cl for _, cl in acc]
    while keep:
        FA = np.stack([fire(Z, cl) for cl in keep], 1).astype(np.uint8); r = table_eval(FA, None, ia, ib)
        print("  %s: batch of %d clauses -> held-set acc %.4f (%+.4f) | Shirt recall %.3f (%+.3f)" % (kind, len(keep), r[0], r[0] - base_B[0], r[1], r[1] - base_B[1]), flush=True)
        if r[1] - base_B[1] >= GAIN and base_B[0] - r[0] <= 0.002: break
        keep = keep[:len(keep) // 2]; print("    batch undone, halved", flush=True)
    return keep
res = {}
for kind in ("hypothesis", "random"):
    keep = run(kind)
    if keep:
        FA = np.stack([fire(Z, cl) for cl in keep], 1).astype(np.uint8); FT = np.stack([fire(Zt, cl) for cl in keep], 1).astype(np.uint8); res[kind] = (len(keep),) + table_eval(FA, FT, np.arange(60000), None, test=True)
    else: res[kind] = (0,) + table_eval(None, None, np.arange(60000), None, test=True)
    print("FINAL %-10s kept %3d clauses | test acc %.4f | Shirt recall %.3f | cluster %.4f | Shirt AP %.3f" % ((kind,) + res[kind]), flush=True)
print("FINAL L alone (no clauses)      | test acc %.4f | Shirt recall %.3f | cluster %.4f | Shirt AP %.3f" % table_eval(None, None, np.arange(60000), None, test=True), flush=True)
