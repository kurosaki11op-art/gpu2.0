"""26 Oct 2026, SIMULATED. Decision-rule variants on the saved staged state (staged_s2.npz): clipped sums, veto strength, per-class offsets from counters. Checks where the old-class accuracy goes."""
import os, sys
os.environ["MODE"] = "none"; os.environ["EP"] = "0"
sys.argv = ["x"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tm_staged2.py")).read().split("if MODE == \"joint\": run")[0]
exec(src)
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/staged_s2.npz"); state, inc_list, inc_n, vinc_list, vinc_n = z["state"], z["inc_list"], z["inc_n"], z["vinc_list"], z["vinc_n"]
so = scores(Xt, inc_list, inc_n).astype(np.float32); sv = np.pad(vscores(Xt, vinc_list, vinc_n).astype(np.float32)[:, :6], ((0, 0), (0, 4))); om = np.isin(yte, OLD)
def rep(nm, sc):
    p = sc.argmax(1); print("%-46s all %.4f | old %.4f | new %.4f" % (nm, (p == yte).mean(), (p[om] == yte[om]).mean(), (p[~om] == yte[~om]).mean()), flush=True)
rep("unclipped, vetoes", so + sv); rep("clipped +-T per class, vetoes", np.clip(so + sv, -T, T)); rep("clipped, no vetoes", np.clip(so, -T, T))
for w in (0.25, 0.5, 0.75): rep("unclipped, veto weight %.2f" % w, so + w * sv)
print("mean class sums on old images: old bank %.1f, new bank %.1f; on new images: old %.1f, new %.1f" % (so[om][:, :6].max(1).mean(), so[om][:, 6:].max(1).mean(), so[~om][:, :6].max(1).mean(), so[~om][:, 6:].max(1).mean()))
for off in (0, 5, 10, 20): sc = so + sv; sc[:, :6] += off; rep("unclipped, vetoes, old-class offset +%d" % off, sc)
# self-calibration: the chip picks the old-class offset using only what it holds in stage 2 (new-class training images and dreams of the old classes), no old real images, no test data
rates = np.stack([X[y == c].mean(0) for c in OLD]).astype(np.float64); outs = np.zeros(C, np.int8); np.random.seed(5)
idx = np.where(np.isin(y, NEW))[0][:4000]; Xn = X[idx]; yn = y[idx]
D = np.stack([dream(c, rates, inc_list, inc_n, outs, True) for c in np.random.randint(0, 6, 4000) for _ in [0]]); dc = None
np.random.seed(5); cs = np.random.randint(0, 6, 4000); D = np.stack([dream(c, rates, inc_list, inc_n, outs, True) for c in cs])
def sc_of(Z): return scores(Z, inc_list, inc_n).astype(np.float32) + np.pad(vscores(Z, vinc_list, vinc_n).astype(np.float32)[:, :6], ((0, 0), (0, 4)))
Sn, Sd = sc_of(Xn), sc_of(D); best = None
for off in range(-5, 31, 5):
    a = lambda S, lab: ((S + np.r_[[off] * 6, [0] * 4]).argmax(1) == lab).mean(); bal = (a(Sn, yn) + a(Sd, cs)) / 2; print("offset %+d: new-train acc %.3f, old-dream acc %.3f, balanced %.3f" % (off, a(Sn, yn), a(Sd, cs), bal), flush=True)
    if best is None or bal > best[0]: best = (bal, off)
sc = so + sv; sc[:, :6] += best[1]; rep("self-calibrated offset %+d" % best[1], sc)
