"""26 Oct 2026, SIMULATED. HARD DREAMS and a label-free offset rule, continuing from the saved veto-trained staged state (staged_s2.npz, made by tm_staged2.py MODE=veto).
The chip imagines: pick an old class c and a new class n, build a dream that is a bit-level mixture of the two classes' stored bit frequencies (the majority source gives the dream's label), and keep it only if the chip is UNSURE about it (its score for the label class is within MARG of its score for the other class): imagining something it cannot tell apart. It then learns the difference: the label class is told (positive feedback: veto bank of an old label, clause bank of a new label), the other class is told "not mine" (new bank negative feedback; veto bank negative feedback for an old other class). Old clauses are never rewritten, only the appended veto bank and the new banks learn.
Label-free offset: pick the old-class offset at which the chip gets hard OLD dreams and hard NEW dreams right equally often (no real images, no labels, no test data).
env: ROUNDS (training passes of NH hard dreams), MARG, LAMLO/LAMHI mixing range."""
import os, sys
os.environ["MODE"] = "none"; os.environ["EP"] = "0"
sys.argv = ["x"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tm_staged2.py")).read().split("if MODE == \"joint\": run")[0]
exec(src)
E_ = lambda k, d: type(d)(os.environ.get(k, d))
ROUNDS = E_("ROUNDS", 3); NH = E_("NH", 20000); MARG = E_("MARG", 10); LAMLO = E_("LAMLO", 0.1); LAMHI = E_("LAMHI", 0.45)
SP = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/"
z = np.load(SP + "staged_s2.npz"); state, inc_list, inc_n, vstate, vinc_list, vinc_n = [z[k].copy() for k in ("state", "inc_list", "inc_n", "vstate", "vinc_list", "vinc_n")]
rates = np.stack([X[y == c].mean(0) for c in range(10)]).astype(np.float64)                      # stored per-class bit frequencies (counters), old from stage 1, new from stage 2
@njit
def total(k, d, state_unused, inc_list, inc_n, vinc_list, vinc_n, outs, vouts):
    s = class_sum(k, d, inc_list, inc_n, outs, False)
    if k < 6: s += class_sum(k, d, vinc_list, vinc_n, vouts, False, 1)
    return s
@njit
def make(c, n, lam, rates):                                                                       # mixture dream: each bit comes from class n's frequency with probability lam, else from class c's
    d = np.zeros(NB, np.uint8)
    for k in range(NB):
        r = rates[n, k] if np.random.random() < lam else rates[c, k]
        d[k] = 1 if np.random.random() < r else 0
    return d
@njit
def hard_pairs(count, rates, inc_list, inc_n, vinc_list, vinc_n, seed, lamlo, lamhi, marg):
    np.random.seed(seed); D = np.zeros((count, NB), np.uint8); lab = np.zeros(count, np.int64); oth = np.zeros(count, np.int64); outs = np.zeros(C, np.int8); vouts = np.zeros(C, np.int8); got = 0; tries = 0
    while got < count and tries < count * 60:
        tries += 1; c = np.random.randint(6); n = 6 + np.random.randint(4); lam = lamlo + (lamhi - lamlo) * np.random.random()
        if np.random.random() < 0.5: d = make(c, n, lam, rates); a = c; b = n                       # mostly old
        else: d = make(n, c, lam, rates); a = n; b = c                                              # mostly new
        sa = total(a, d, 0, inc_list, inc_n, vinc_list, vinc_n, outs, vouts); sb = total(b, d, 0, inc_list, inc_n, vinc_list, vinc_n, outs, vouts)
        if abs(sa - sb) <= marg: D[got] = d; lab[got] = a; oth[got] = b; got += 1
    return D[:got], lab[:got], oth[:got]
@njit
def learn_hard(D, lab, oth, state, inc_list, inc_n, vstate, vinc_list, vinc_n, seed):
    np.random.seed(seed); outs = np.zeros(C, np.int8); outs2 = np.zeros(C, np.int8); vouts = np.zeros(C, np.int8)
    for i in range(len(D)):
        d = D[i]; a = lab[i]; b = oth[i]
        for role in range(2):
            k = a if role == 0 else b; pos = (role == 0)
            if k >= 6: v = max(-T, min(T, class_sum(k, d, inc_list, inc_n, outs, False))); feedback(k, d, state, inc_list, inc_n, outs, v, pos)       # new bank
            else:
                vo = class_sum(k, d, inc_list, inc_n, outs2, True); vv = class_sum(k, d, vinc_list, vinc_n, vouts, False, 2); v = max(-T, min(T, vo + vv))
                feedback(k, d, vstate, vinc_list, vinc_n, vouts, v, pos, 1)                          # old class: veto bank learns (mine / not mine)
def sc_of(Z): return scores(Z, inc_list, inc_n).astype(np.float32) + np.pad(vscores(Z, vinc_list, vinc_n).astype(np.float32)[:, :6], ((0, 0), (0, 4)))
om = np.isin(yte, OLD)
def rep(nm, sc):
    p = sc.argmax(1); print("%-50s all %.4f | old %.4f | new %.4f | Shirt recall %.3f" % (nm, (p == yte).mean(), (p[om] == yte[om]).mean(), (p[~om] == yte[~om]).mean(), (p[yte == 6] == 6).mean()), flush=True)
def offset_rule(seed):                                                                              # label-free: equalise hard-old and hard-new dream accuracy
    D, lab, oth = hard_pairs(4000, rates, inc_list, inc_n, vinc_list, vinc_n, seed, LAMLO, LAMHI, 10 ** 6); S = sc_of(D); best = None
    for off in range(-10, 41, 2):
        S2 = S.copy(); S2[:, :6] += off; p = S2.argmax(1); ao = (p[lab < 6] == lab[lab < 6]).mean(); an = (p[lab >= 6] == lab[lab >= 6]).mean()
        if best is None or abs(ao - an) < best[0]: best = (abs(ao - an), off, ao, an)
    print("  label-free offset rule: offset %+d (hard-old dream acc %.3f, hard-new dream acc %.3f)" % (best[1], best[2], best[3]), flush=True); return best[1]
S0 = sc_of(Xt); rep("before hard dreams", S0); off0 = offset_rule(11); S1 = S0.copy(); S1[:, :6] += off0; rep("before, with label-free offset", S1)
for r in range(ROUNDS):
    D, lab, oth = hard_pairs(NH, rates, inc_list, inc_n, vinc_list, vinc_n, 100 + r, LAMLO, LAMHI, MARG); learn_hard(D, lab, oth, state, inc_list, inc_n, vstate, vinc_list, vinc_n, 200 + r)
    S = sc_of(Xt); print("round %d: %d unsure dreams (%.0f%% old-labelled)" % (r + 1, len(D), 100 * (lab < 6).mean()), flush=True); rep("  after round %d" % (r + 1), S)
off = offset_rule(12); S2 = S.copy(); S2[:, :6] += off; rep("after, with label-free offset %+d" % off, S2)
for o in (0, 5, 10): S3 = S.copy(); S3[:, :6] += o; rep("  after, fixed offset %+d (for reference)" % o, S3)
