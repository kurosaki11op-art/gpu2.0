"""26 Oct 2026, SIMULATED. Piece 1 + 3 of the memory-cost plan. PICK=kmeans chooses the E stored images per old class as the images nearest to E cluster centres of the class (coverage of its variety, not outliers); AUG=cross draws each rehearsal image as a recombination of two stored images of the same class (each differing bit taken from either parent) plus FLIP bit noise, so a handful of images cannot be memorised as exceptions; AUG=flip is noise only.\nUnfrozen rehearsal: stage 1 (classes 0-5) is loaded, then ALL ten banks keep learning with the ordinary local clause rule on a class-balanced stream: new classes from their full data, old classes only from E stored real images each (random). Nothing is frozen; old clauses can be refined. Memory = E images per old class. env: E, STEPS."""
import os, sys
os.environ["MODE"] = "none"; os.environ["EP"] = "0"
sys.argv = ["x"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tm_staged2.py")).read().split("if MODE == \"joint\": run")[0]
exec(src)
E_ = lambda k, d: type(d)(os.environ.get(k, d)); NE = E_("E", 20); STEPS = E_("STEPS", 150000); PICK = E_("PICK", "random"); AUG = E_("AUG", "none"); FLIP = E_("FLIP", 0.02); PL = E_("PL", 1.0)
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/staged_s1.npz"); state[:] = z["state"]; inc_list[:] = z["inc_list"]; inc_n[:] = z["inc_n"]
rs = np.random.RandomState(3)
def pick_kmeans(ids, k):
    A = X[ids].astype(np.float32); cen = A[rs.choice(len(A), k, replace=False)].copy(); an = (A * A).sum(1)
    for it in range(8):
        d = an[:, None] - 2 * A @ cen.T + (cen * cen).sum(1)[None, :]; lab = d.argmin(1)
        for j in range(k):
            if (lab == j).any(): cen[j] = A[lab == j].mean(0)
    d = an[:, None] - 2 * A @ cen.T + (cen * cen).sum(1)[None, :]; return np.array([ids[d[:, j].argmin()] for j in range(k)])
EX = np.stack([X[pick_kmeans(np.where(y == c)[0], NE) if PICK == "kmeans" else rs.choice(np.where(y == c)[0], NE, replace=False)] for c in OLD])      # (6, NE, NB)
newidx = [np.where(y == c)[0] for c in NEW]
@njit
def stream(Xs, newcls_idx, EX, state, inc_list, inc_n, steps, seed, aug, flip, pl):
    np.random.seed(seed); outs = np.zeros(C, np.int8); outs2 = np.zeros(C, np.int8)
    for s in range(steps):
        a = np.random.randint(10)
        if a < 6:
            x = EX[a, np.random.randint(EX.shape[1])].copy()
            if aug >= 1:
                if aug == 2:
                    x2 = EX[a, np.random.randint(EX.shape[1])]
                    for k in range(len(x)):
                        if x[k] != x2[k] and np.random.random() < 0.5: x[k] = x2[k]
                for k in range(len(x)):
                    if np.random.random() < flip: x[k] = 1 - x[k]
        else: x = Xs[newcls_idx[a - 6, np.random.randint(newcls_idx.shape[1])]]
        v = class_sum(a, x, inc_list, inc_n, outs, True)
        if a >= 6 or np.random.random() < pl: feedback(a, x, state, inc_list, inc_n, outs, v, True)
        o = (a + 1 + np.random.randint(9)) % 10
        v2 = class_sum(o, x, inc_list, inc_n, outs2, True)
        if o >= 6 or np.random.random() < pl: feedback(o, x, state, inc_list, inc_n, outs2, v2, False)
minlen = min(len(i) for i in newidx); NI = np.stack([i[:minlen] for i in newidx]); om = np.isin(yte, OLD)
for r in range(STEPS // 50000):
    stream(X, NI, EX, state, inc_list, inc_n, 50000, 11 + r, 0 if AUG == 'none' else (1 if AUG == 'flip' else 2), FLIP, PL); so = scores(Xt, inc_list, inc_n).astype(np.float32)
    for off in (0, 10, 20, 30, 40):
        s_ = so.copy(); s_[:, :6] += off; p = s_.argmax(1); print("RESULT rehearse %s %s PL=%.2f E=%d steps %d offset %+d: all %.4f | old %.4f | new %.4f | Shirt recall %.3f | share predicted old %.3f (true 0.600)" % (PICK, AUG, PL, NE, 50000 * (r + 1), off, (p == yte).mean(), (p[om] == yte[om]).mean(), (p[~om] == yte[~om]).mean(), (p[yte == 6] == 6).mean(), (p < 6).mean()), flush=True)
