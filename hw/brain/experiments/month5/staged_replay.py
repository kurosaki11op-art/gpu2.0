"""26 Oct 2026, SIMULATED. Boundary memory: after stage 1 the chip keeps E real images per old class, the ones it was MOST UNSURE about (smallest margin between its own class sum and the best other old class sum) or, as a control, E random ones. In stage 2 these stored images replace the dreams: new banks use them as negatives, the old classes' veto banks use them as 'still mine', new-class images as 'not mine'. Old clauses never rewritten.
env: E (examples per old class), PICK (doubt|random), EP (epochs, default 2). Stage 1 state is loaded from staged_s1.npz (made by tm_staged2.py)."""
import os, sys
os.environ["MODE"] = "none"; os.environ["EP"] = "0"
sys.argv = ["x"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tm_staged2.py")).read().split("if MODE == \"joint\": run")[0]
exec(src)
E_ = lambda k, d: type(d)(os.environ.get(k, d)); NE = E_("E", 5); PICK = E_("PICK", "doubt"); EPS = E_("EPS", 2)
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/staged_s1.npz"); state[:] = z["state"]; inc_list[:] = z["inc_list"]; inc_n[:] = z["inc_n"]
oi = np.where(np.isin(y, OLD))[0]; s1 = scores(X[oi], inc_list, inc_n).astype(np.float32)[:, :6]; yo = y[oi]
own = s1[np.arange(len(oi)), yo]; oth = s1.copy(); oth[np.arange(len(oi)), yo] = -1e9; marg = own - oth.max(1)
EX = []; EY = []; rs = np.random.RandomState(3)
for c in OLD:
    ids = np.where(yo == c)[0]; pick = ids[np.argsort(marg[ids])[:NE]] if PICK == "doubt" else rs.choice(ids, NE, replace=False)
    EX.append(X[oi[pick]]); EY += [c] * NE
EX = np.concatenate(EX); EY = np.array(EY); print("stored %d images (%s), %.1f KB as bit lists" % (len(EX), PICK, len(EX) * (EX.sum(1).mean() * 2 / 1024)), flush=True)
@njit
def train_rep(Xs, ys, order, classes, EX, EY, state, inc_list, inc_n, seed):
    np.random.seed(seed); outs = np.zeros(C, np.int8); outs2 = np.zeros(C, np.int8); nc = len(classes)
    for ii in range(len(order)):
        i = order[ii]; x = Xs[i]; a = ys[i]
        v = class_sum(a, x, inc_list, inc_n, outs, True); feedback(a, x, state, inc_list, inc_n, outs, v, True)
        o = classes[np.random.randint(nc)]
        while o == a: o = classes[np.random.randint(nc)]
        v2 = class_sum(o, x, inc_list, inc_n, outs2, True); feedback(o, x, state, inc_list, inc_n, outs2, v2, False)
        if np.random.random() < 0.5:                                                                # a stored real old image is NOT a new class; and a stored image is the right answer for its own class? (old banks frozen, so only negatives)
            d = EX[np.random.randint(len(EX))]; n = classes[np.random.randint(nc)]
            v3 = class_sum(n, d, inc_list, inc_n, outs2, True); feedback(n, d, state, inc_list, inc_n, outs2, v3, False)
@njit
def veto_rep(Xs, order, EX, EY, state, inc_list, inc_n, vstate, vinc_list, vinc_n, seed):
    np.random.seed(seed); outs = np.zeros(C, np.int8); outs2 = np.zeros(C, np.int8); vouts = np.zeros(C, np.int8)
    for ii in range(len(order)):
        x = Xs[order[ii]]; c = np.random.randint(6)
        vo = class_sum(c, x, inc_list, inc_n, outs, True); vv = class_sum(c, x, vinc_list, vinc_n, vouts, False, 2); v = max(-T, min(T, vo + vv))
        feedback(c, x, vstate, vinc_list, vinc_n, vouts, v, False, 1)                                # new image: not this old class
        j = np.random.randint(len(EX)); d = EX[j]; c = EY[j]
        vo = class_sum(c, d, inc_list, inc_n, outs2, True); vv = class_sum(c, d, vinc_list, vinc_n, vouts, False, 2); v = max(-T, min(T, vo + vv))
        feedback(c, d, vstate, vinc_list, vinc_n, vouts, v, True, 1)                                 # stored real image of this old class: still mine
idx = np.where(np.isin(y, NEW))[0]; om = np.isin(yte, OLD)
for e in range(EPS): train_rep(X, y, np.random.RandomState(100 + e).permutation(idx), np.array(NEW), EX, EY, state, inc_list, inc_n, 1000 + e)
vstate = np.full((6 * C, NL), NST, np.uint8); vinc_list = np.zeros((6 * C, LMAX), np.int32); vinc_n = np.zeros(6 * C, np.int32)
for e in range(EPS): veto_rep(X, np.random.RandomState(7 + e).permutation(idx), EX, EY, state, inc_list, inc_n, vstate, vinc_list, vinc_n, 500 + e)
so = scores(Xt, inc_list, inc_n).astype(np.float32); sv = np.pad(vscores(Xt, vinc_list, vinc_n).astype(np.float32)[:, :6], ((0, 0), (0, 4)))
for nm, sc in (("no vetoes", so), ("with vetoes", so + sv)):
    for off in (0, 5, 10):
        s_ = sc.copy(); s_[:, :6] += off; p = s_.argmax(1); print("RESULT E=%d %s | %-12s offset %+d: all %.4f | old %.4f | new %.4f | Shirt recall %.3f" % (NE, PICK, nm, off, (p == yte).mean(), (p[om] == yte[om]).mean(), (p[~om] == yte[~om]).mean(), (p[yte == 6] == 6).mean()), flush=True)
