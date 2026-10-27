"""26 Oct 2026, SIMULATED. PART 4 of the research plan: PROGRESS-RANKED REHEARSAL (research note 4, Design A) replacing the hand-set pair weights of the controller below. Per-class DOUBT on the unlabeled probe (share of probe images predicted as class c whose top-2 margin is small) is tracked per chunk; learning progress of class c = its drop in doubt; class sampling weights = 0.2 uniform + 0.8 * normalised noisy |progress| (Thompson-like, fixed uniform floor); the night ends when total |progress| stays below EPS for 2 chunks; every chunk prints a decision log (weights and why). Set-points are READ-ONLY constants (balance target 1/10 per class, alarm threshold). Tripwire and undo as before. Compare with CTRL=0 (uniform stream, 8 chunks) and the earlier pair-weight controller.\n\nA CONTROLLER that lets the chip run its own learning loop during stage 2 (Fashion-MNIST, 6 old classes + 4 new, unfrozen rehearsal from E stored recombined images per old class), using only unlabeled signals it holds:
 (4) NOTICE: after every chunk it classifies an unlabeled probe set (5,000 images, labels never used) and compares the share of images assigned to each class with the share expected from its own stream (1/10 each). If the share distance grows by more than ALARM over the best so far it treats the chunk as harmful, restores the checkpoint from before the chunk and halves the learning rate of the chunk (fewer steps).
 (1) DECIDE: the old/new offset is set every chunk by matching the predicted old share to the stream share; it stops (decides how much) when the share distance and the confusion have not improved for 2 chunks; which classes to rehearse next is chosen from the probe: the pairs of classes that most often are the top two with a small margin get extra sampling weight.
 (2) COMPARE: the extra weight on the confused pair means the clauses of both classes are trained on both classes' images (conjunctions are learned by the clause rule), instead of counting single bits.
SABOTAGE=1 corrupts the rehearsal images (40% bit noise) in chunk 3 to test whether the chip notices and recovers. CTRL=0 runs the same chunks with none of the above (uniform stream, fixed offset by the same share rule at the end only).
Evaluation (labels used only for scoring): the other 5,000 test images. env: E, CTRL, SABOTAGE, CHUNK, NCH."""
import os, sys
os.environ["MODE"] = "none"; os.environ["EP"] = "0"
sys.argv = ["x"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tm_staged2.py")).read().split("if MODE == \"joint\": run")[0]
exec(src)
E_ = lambda k, d: type(d)(os.environ.get(k, d)); NE = E_("E", 20); CTRL = E_("CTRL", 1); SAB = E_("SABOTAGE", 0); CHUNK = E_("CHUNK", 25000); NCH = E_("NCH", 8); ALARM = E_("ALARM", 0.05)
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/staged_s1.npz"); state[:] = z["state"]; inc_list[:] = z["inc_list"]; inc_n[:] = z["inc_n"]
rs = np.random.RandomState(3); EX = np.stack([X[rs.choice(np.where(y == c)[0], NE, replace=False)] for c in OLD]); newidx = [np.where(y == c)[0] for c in NEW]; minlen = min(len(i) for i in newidx); NI = np.stack([i[:minlen] for i in newidx])
@njit
def stream(Xs, newcls_idx, EX, state, inc_list, inc_n, steps, seed, flip, cw):
    np.random.seed(seed); outs = np.zeros(C, np.int8); outs2 = np.zeros(C, np.int8); tot = cw.sum()
    for s in range(steps):
        r = np.random.random() * tot; a = 0; acc = cw[0]
        while acc < r and a < 9: a += 1; acc += cw[a]
        if a < 6:
            x = EX[a, np.random.randint(EX.shape[1])].copy(); x2 = EX[a, np.random.randint(EX.shape[1])]
            for k in range(len(x)):
                if x[k] != x2[k] and np.random.random() < 0.5: x[k] = x2[k]
                if np.random.random() < flip: x[k] = 1 - x[k]
        else: x = Xs[newcls_idx[a - 6, np.random.randint(newcls_idx.shape[1])]]
        v = class_sum(a, x, inc_list, inc_n, outs, True); feedback(a, x, state, inc_list, inc_n, outs, v, True)
        o = (a + 1 + np.random.randint(9)) % 10
        if np.random.random() < 0.5:                                                                  # a confusable partner gets the negative feedback more often
            best = -10 ** 6; o2 = o
            for k in range(10):
                if k != a and cw[k] > 1.5:
                    sk = class_sum(k, x, inc_list, inc_n, outs2, False)
                    if sk > best: best = sk; o2 = k
            o = o2
        v2 = class_sum(o, x, inc_list, inc_n, outs2, True); feedback(o, x, state, inc_list, inc_n, outs2, v2, False)
PR, EV = np.arange(5000), np.arange(5000, 10000); Xp = Xt[PR]; Xe = Xt[EV]; ye = yte[EV]; om = np.isin(ye, OLD)
def probe(offset_rule=True):
    sc = scores(Xp, inc_list, inc_n).astype(np.float32); best = (9, 0)
    for off in range(0, 61, 2):
        s_ = sc.copy(); s_[:, :6] += off; sh = (s_.argmax(1) < 6).mean(); d = abs(sh - 0.6)
        if d < best[0]: best = (d, off)
    off = best[1]; s_ = sc.copy(); s_[:, :6] += off; p = s_.argmax(1); share = np.bincount(p, minlength=10) / len(p); srt = np.argsort(-s_, 1); marg = s_[np.arange(len(s_)), srt[:, 0]] - s_[np.arange(len(s_)), srt[:, 1]]
    small = marg <= np.quantile(marg, 0.25); conf = np.zeros((10, 10)); 
    for a_, b_ in zip(srt[small, 0], srt[small, 1]): conf[a_, b_] += 1
    pair = np.triu(conf + conf.T, 1); return off, share, np.abs(share - 0.1).sum(), pair
def doubt_per_class(off):
    sc = scores(Xp, inc_list, inc_n).astype(np.float32); sc[:, :6] += off; srt = np.sort(sc, 1); marg = srt[:, -1] - srt[:, -2]; p = sc.argmax(1); small = marg <= np.quantile(marg, 0.25)
    return np.array([small[p == c].mean() if (p == c).sum() > 20 else 0.5 for c in range(10)])
def mem_acc(off):                                                                                   # the chip's own stored rehearsal images (labels known to it): old-class accuracy, an independent harm signal
    sc = scores(EX.reshape(-1, NB), inc_list, inc_n).astype(np.float32); sc[:, :6] += off; return (sc.argmax(1) == np.repeat(np.arange(6), EX.shape[1])).mean()
def evaluate(tag, off):
    s_ = scores(Xe, inc_list, inc_n).astype(np.float32); s_[:, :6] += off; p = s_.argmax(1)
    print("EVAL %-34s offset %+d: all %.4f | old %.4f | new %.4f | Shirt recall %.3f" % (tag, off, (p == ye).mean(), (p[om] == ye[om]).mean(), (p[~om] == ye[~om]).mean(), (p[ye == 6] == 6).mean()), flush=True)
cw = np.ones(10); prev_doubt = None; calm = 0; hist = []; best_mem = 0.0; MEMDROP = E_('MEMDROP', 0.0); EPS = 0.01; MINCH = E_("MINCH", 6); rng = np.random.RandomState(5); best_d = 9.0; ck = (state.copy(), inc_list.copy(), inc_n.copy()); stale = 0; lr_div = 1; log = []
off, share, d0, pair = probe(); print("start: offset %+d, share distance %.3f" % (off, d0), flush=True); evaluate("start (stage 1 + nothing)", off); best_d = d0
for ch in range(NCH):
    flip = 0.45 if (SAB and ch == E_('SABCH', 2)) else 0.02; steps = CHUNK // lr_div
    stream(X, NI, EX, state, inc_list, inc_n, steps, 11 + ch, flip, cw); off, share, d, pair = probe()
    msg = "chunk %d (%d steps, flip %.2f%s): share distance %.3f, offset %+d" % (ch + 1, steps, flip, " SABOTAGED" if flip > 0.1 else "", d, off)
    if CTRL:
        spread = max(0.01, float(np.median(np.abs(np.diff(hist))))) if len(hist) >= 3 else None
        thr = ALARM if (spread is None or E_('ALARMMODE', 'fixed') == 'fixed') else max(0.04, 4 * spread)
        ma = mem_acc(off) if MEMDROP > 0 else 1.0
        if d > best_d + thr or (MEMDROP > 0 and best_mem - ma > MEMDROP):
            state[:], inc_list[:], inc_n[:] = ck; lr_div = min(lr_div * 2, 4); cw[:] = 1; msg += " -> ALARM: share distance rose by %.3f (threshold %.3f), stored-image accuracy %.3f (best %.3f), chunk undone, step size halved" % (d - best_d, thr, ma, best_mem); off, share, d, pair = probe()
        else:
            best_mem = max(best_mem, ma); ck = (state.copy(), inc_list.copy(), inc_n.copy()); stale = 0 if d < best_d - 0.005 else stale + 1; best_d = min(best_d, d)
            dn = doubt_per_class(off)
            if prev_doubt is not None:
                prog = np.maximum(prev_doubt - dn, 0) + 0.25 * np.maximum(dn - prev_doubt, 0); noisy = prog * rng.gamma(2.0, 0.5, 10) + 1e-6
                cw = 0.2 / 10 + 0.8 * noisy / noisy.sum(); cw = cw / cw.mean(); tot = np.abs(prev_doubt - dn).sum(); calm = calm + 1 if tot < EPS * 10 else 0
                msg += " -> ok; progress %s; weights %s" % (np.round(prog, 3).tolist(), np.round(cw, 2).tolist())
            else: msg += " -> ok; first chunk, uniform"
            prev_doubt = dn; hist.append(d)
    print(msg, flush=True); evaluate("after chunk %d" % (ch + 1), off)
    if CTRL and ch + 1 >= MINCH and (stale >= 2 or calm >= 2): print("STOP: no progress or no improvement for 2 chunks (chip decides it is done)", flush=True); break
off, share, d, pair = probe(); evaluate("FINAL", off)
