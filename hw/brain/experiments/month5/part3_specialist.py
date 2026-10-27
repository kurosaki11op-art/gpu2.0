"""27 Oct 2026, SIMULATED. Part 3 retried as a WIN attempt: the hypothesis 'these four classes need their own, stronger look' built from our own primitives: a clause specialist (Tsetlin-style, no matrix, no backprop) trained ONLY on T-shirt, Pullover, Coat and Shirt over L's code + raw pixel bits, many clauses per class, then used as a second look on the images L assigns to that group (hard replacement inside the group, or a sum of z-scored scores). Reference ceiling from part3_ceiling.py: dense network 4-way Shirt recall 0.74, L's table 0.687.
env: CC clauses per class, TT, EP epochs."""
import os, sys
os.environ["MODE"] = "none"; os.environ["EP"] = "0"
sys.argv = ["x"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tm_staged2.py")).read().split("if MODE == \"joint\": run")[0]
exec(src)
from shirt_new_methods_setup import train_table, CL
EPS_ = int(os.environ.get("EPS", 5)); GROUP = np.array([0, 2, 4, 6]); idx = np.where(np.isin(y, GROUP))[0]; mt = np.isin(yte, GROUP)
W = train_table(ctr, ytr); SL = cte.astype(np.int32) @ W; pL = SL.argmax(1)
print("L alone: acc %.4f | Shirt recall %.3f | group 4-way acc %.4f | 4-way Shirt recall %.3f" % ((pL == yte).mean(), (pL[yte == 6] == 6).mean(), (SL[mt][:, GROUP].argmax(1) == np.searchsorted(GROUP, yte[mt])).mean(), (SL[mt][:, GROUP].argmax(1)[yte[mt] == 6] == 3).mean()), flush=True)
def report(tag):
    S = scores(Xt, inc_list, inc_n).astype(np.float32)[:, GROUP]; ye = np.searchsorted(GROUP, yte[mt]); p4 = S[mt].argmax(1)
    print("[%s] specialist alone, 4-way: acc %.4f | Shirt recall %.3f" % (tag, (p4 == ye).mean(), (p4[ye == 3] == 3).mean()), flush=True)
    ing = np.isin(pL, GROUP); Sg = S.copy(); b = np.zeros(4)
    for _ in range(60):                                                                             # label-free balancing: inside the group each class should get about a quarter of the predictions
        sh = np.bincount((Sg[ing] + b).argmax(1), minlength=4) / ing.sum(); b += 4.0 * (0.25 - sh)
    Sb = S + b; p4b = Sb[mt].argmax(1); print("     balanced offsets %s: specialist 4-way acc %.4f | Shirt recall %.3f" % (np.round(b, 1).tolist(), (p4b == ye).mean(), (p4b[ye == 3] == 3).mean()), flush=True)
    for nm in ("hard-balanced",):
        p = pL.copy(); p[ing] = GROUP[Sb[ing].argmax(1)]; print("     cascade (%s): acc %.4f | Shirt recall %.3f" % (nm, (p == yte).mean(), (p[yte == 6] == 6).mean()), flush=True)
    zb = lambda A: (A - A.mean(1, keepdims=True)) / (A.std() + 1e-9); comb = zb(SL[:, GROUP].astype(np.float32)) + zb(Sb); p = pL.copy(); p[ing] = GROUP[comb[ing].argmax(1)]; print("     cascade (soft-balanced): acc %.4f | Shirt recall %.3f" % ((p == yte).mean(), (p[yte == 6] == 6).mean()), flush=True)
    z = lambda A: (A - A.mean(1, keepdims=True)) / (A.std() + 1e-9)
    for nm in ("hard", "soft"):
        p = pL.copy()
        if nm == "hard": p[ing] = GROUP[S[ing].argmax(1)]
        else: comb = z(SL[:, GROUP].astype(np.float32)) + z(S); p[ing] = GROUP[comb[ing].argmax(1)]
        print("     cascade (%s): acc %.4f | Shirt recall %.3f | group acc %.4f" % (nm, (p == yte).mean(), (p[yte == 6] == 6).mean(), (np.where(np.isin(yte, GROUP), p == yte, False).sum() / mt.sum())), flush=True)
for e in range(EPS_):
    train(X, y, np.random.RandomState(100 + e).permutation(idx), GROUP, np.zeros((1, NB)), 0.0, state, inc_list, inc_n, 1000 + e + 7 * int(os.environ.get('SD', 0))); report("epoch %d" % (e + 1))
# the recipe that worked for the all-class clause layer: the specialist's clauses become extra input bits of L's counting table
@njit(parallel=True)
def fire_group(Xs, inc_list, inc_n, cls_ids):
    out = np.zeros((len(Xs), len(cls_ids) * C), np.uint8)
    for i in prange(len(Xs)):
        for a in range(len(cls_ids)):
            for j in range(C):
                cl = cls_ids[a] * C + j; n = inc_n[cl]; ok = 1 if n > 0 else 0
                for t in range(n):
                    lit = inc_list[cl, t]
                    if lit < NB:
                        if Xs[i, lit] == 0: ok = 0; break
                    elif Xs[i, lit - NB] == 1: ok = 0; break
                out[i, a * C + j] = ok
    return out
ftr = np.concatenate([fire_group(X[i:i + 5000], inc_list, inc_n, GROUP) for i in range(0, len(X), 5000)]); fte = fire_group(Xt, inc_list, inc_n, GROUP)
Wc = train_table(np.concatenate([ctr, ftr], 1), ytr); Sc = np.concatenate([cte, fte], 1).astype(np.int32) @ Wc; pc = Sc.argmax(1); mk = np.isin(yte, CL); s6 = Sc[:, 6] - np.delete(Sc, 6, 1).max(1); yy = yte == 6; o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
print("L + specialist clause bits in the table (%d clauses, %.0f fire per image): acc %.4f | Shirt recall %.3f | cluster %.4f | Shirt AP %.3f   [L alone: 0.8885 | 0.638 | 0.8063 | 0.753]" % (ftr.shape[1], fte.sum(1).mean(), (pc == yte).mean(), (pc[yte == 6] == 6).mean(), (CL[Sc[mk][:, CL].argmax(1)] == yte[mk]).mean(), ap), flush=True)

# routed version: the specialist's clauses are only evaluated (bits non-zero) for images that L's own table assigns to the group
Wl = train_table(ctr, ytr); ing_tr = np.isin((ctr.astype(np.int32) @ Wl).argmax(1), GROUP); ing_te = np.isin(pL, GROUP)
Wr = train_table(np.concatenate([ctr, ftr * ing_tr[:, None]], 1), ytr); Sr = np.concatenate([cte, fte * ing_te[:, None]], 1).astype(np.int32) @ Wr; pr = Sr.argmax(1); s6 = Sr[:, 6] - np.delete(Sr, 6, 1).max(1); o = np.argsort(-s6, kind="stable"); tp = np.cumsum(yy[o]); ap = ((tp / np.arange(1, len(o) + 1)) * yy[o]).sum() / yy.sum()
print("ROUTED (specialist evaluated only on the %.0f%% of images L assigns to the group; %.0f clauses fire per image on average): acc %.4f | Shirt recall %.3f | cluster %.4f | Shirt AP %.3f" % (100 * ing_te.mean(), (fte * ing_te[:, None]).sum(1).mean(), (pr == yte).mean(), (pr[yte == 6] == 6).mean(), (CL[Sr[mk][:, CL].argmax(1)] == yte[mk]).mean(), ap), flush=True)
