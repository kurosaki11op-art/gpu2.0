"""26 Oct 2026, SIMULATED. Unfrozen rehearsal: stage 1 (classes 0-5) is loaded, then ALL ten banks keep learning with the ordinary local clause rule on a class-balanced stream: new classes from their full data, old classes only from E stored real images each (random). Nothing is frozen; old clauses can be refined. Memory = E images per old class. env: E, STEPS."""
import os, sys
os.environ["MODE"] = "none"; os.environ["EP"] = "0"
sys.argv = ["x"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tm_staged2.py")).read().split("if MODE == \"joint\": run")[0]
exec(src)
E_ = lambda k, d: type(d)(os.environ.get(k, d)); NE = E_("E", 20); STEPS = E_("STEPS", 150000)
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/staged_s1.npz"); state[:] = z["state"]; inc_list[:] = z["inc_list"]; inc_n[:] = z["inc_n"]
rs = np.random.RandomState(3); EX = np.stack([X[rs.choice(np.where(y == c)[0], NE, replace=False)] for c in OLD])      # (6, NE, NB)
newidx = [np.where(y == c)[0] for c in NEW]
@njit
def stream(Xs, newcls_idx, EX, state, inc_list, inc_n, steps, seed):
    np.random.seed(seed); outs = np.zeros(C, np.int8); outs2 = np.zeros(C, np.int8)
    for s in range(steps):
        a = np.random.randint(10)
        if a < 6: x = EX[a, np.random.randint(EX.shape[1])]
        else: x = Xs[newcls_idx[a - 6, np.random.randint(newcls_idx.shape[1])]]
        v = class_sum(a, x, inc_list, inc_n, outs, True); feedback(a, x, state, inc_list, inc_n, outs, v, True)
        o = (a + 1 + np.random.randint(9)) % 10
        v2 = class_sum(o, x, inc_list, inc_n, outs2, True); feedback(o, x, state, inc_list, inc_n, outs2, v2, False)
minlen = min(len(i) for i in newidx); NI = np.stack([i[:minlen] for i in newidx]); om = np.isin(yte, OLD)
for r in range(STEPS // 50000):
    stream(X, NI, EX, state, inc_list, inc_n, 50000, 11 + r); so = scores(Xt, inc_list, inc_n).astype(np.float32)
    for off in (-5, 0, 5, 10):
        s_ = so.copy(); s_[:, :6] += off; p = s_.argmax(1); print("RESULT rehearse E=%d steps %d offset %+d: all %.4f | old %.4f | new %.4f | Shirt recall %.3f" % (NE, 50000 * (r + 1), off, (p == yte).mean(), (p[om] == yte[om]).mean(), (p[~om] == yte[~om]).mean(), (p[yte == 6] == 6).mean()), flush=True)
