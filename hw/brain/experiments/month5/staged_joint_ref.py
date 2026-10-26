"""26 Oct 2026, SIMULATED. Stable joint reference with the same code and scoring as the staged tests: all ten classes trained together (300 clauses per class, 4 epochs), then the same old-class offset sweep, so staged and joint are compared along the same old/new frontier."""
import os, sys
os.environ["MODE"] = "none"; os.environ["EP"] = "0"
sys.argv = ["x"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tm_staged2.py")).read().split("if MODE == \"joint\": run")[0]
exec(src)
om = np.isin(yte, OLD)
for e in range(4):
    order = np.random.RandomState(100 + e).permutation(len(X)); train(X, y, order, np.arange(10), np.zeros((1, NB)), 0.0, state, inc_list, inc_n, 1000 + e)
    so = scores(Xt, inc_list, inc_n).astype(np.float32)
    for off in (-10, -5, 0, 5, 10):
        s_ = so.copy(); s_[:, :6] += off; p = s_.argmax(1); print("RESULT joint epoch %d offset %+d: all %.4f | old %.4f | new %.4f | Shirt recall %.3f" % (e + 1, off, (p == yte).mean(), (p[om] == yte[om]).mean(), (p[~om] == yte[~om]).mean(), (p[yte == 6] == 6).mean()), flush=True)
