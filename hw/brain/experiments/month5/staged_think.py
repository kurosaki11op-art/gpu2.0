"""26 Oct 2026, SIMULATED. THINK loop without imagination: the difference between an old class c and a new class n is found by COMPARING STORED COUNTS (per-class bit frequencies, real data, no sampling, no dreams).
Notice: new class n's images are claimed by old class c (c is the nearest known class). Compare: bits that are common in n but rare in c. Hypothesis: 'bit on (or off) means not c' as a one-literal veto clause under c. Test with a GUARANTEE from the counters: a clause that fires only if its literal holds can fire on at most f_c(literal) of c's own images, so vetoes are admitted only if f_c <= RHO (expected damage to the old class at most RHO per veto, known before it is installed). Keep: the K best by how often they fire on the new class (f_n). Old clauses are never touched; the veto bank is appended memory; the new banks are the saved ones from tm_staged2.py (MODE=veto).
env: RHO, K (vetoes per old class and new class), WEIGHT unused."""
import os, sys
os.environ["MODE"] = "none"; os.environ["EP"] = "0"
sys.argv = ["x"]
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tm_staged2.py")).read().split("if MODE == \"joint\": run")[0]
exec(src)
E_ = lambda k, d: type(d)(os.environ.get(k, d)); RHO = E_("RHO", 0.05); K = E_("K", 40)
z = np.load("/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/staged_s2.npz"); state, inc_list, inc_n = z["state"], z["inc_list"], z["inc_n"]
f = np.stack([X[y == c].mean(0) for c in range(10)]); om = np.isin(yte, OLD)
def build(rho, k, claims=True):
    vil = np.zeros((6 * C, LMAX), np.int32); vin = np.zeros(6 * C, np.int32)
    for c in range(6):
        used = 0; fc = np.concatenate([f[c], 1 - f[c]])                                              # probability literal holds in class c (positive, then negated)
        for n in range(6, 10):
            fn = np.concatenate([f[n], 1 - f[n]]); ok = fc <= rho; sc = np.where(ok, fn, -1.0)
            for lit in np.argsort(-sc)[:k]:
                if sc[lit] < 0.05 or used >= C: break
                vil[c * C + used, 0] = lit; vin[c * C + used] = 1; used += 1
    return vil, vin
so = scores(Xt, inc_list, inc_n).astype(np.float32)
def rep(nm, sc):
    p = sc.argmax(1); print("%-52s all %.4f | old %.4f | new %.4f | Shirt recall %.3f" % (nm, (p == yte).mean(), (p[om] == yte[om]).mean(), (p[~om] == yte[~om]).mean(), (p[yte == 6] == 6).mean()), flush=True)
rep("new banks only (no veto)", so)
for rho in (0.01, 0.03, 0.1, 0.3):
    for k in (20, 75):
        vil, vin = build(rho, k); sv = np.pad(vscores(Xt, vil, vin).astype(np.float32)[:, :6], ((0, 0), (0, 4))); rep("counted vetoes rho %.2f, %d per new class (%d total)" % (rho, k, vin.sum()), so + sv)
        fire_old = (-vscores(Xt, vil, vin)[om][:, :6]); own = np.array([fire_old[i, yte[om][i]] for i in range(om.sum())]); print("    vetoes firing on an old image's OWN class: %.2f of %d" % (own.mean(), vin[:C].sum()), flush=True)
