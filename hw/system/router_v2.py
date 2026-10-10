"""Router, round 2 (chip design unchanged; host-side software only).
1) Request router: features of SPARK's outputs over a 128-byte request -> predicted SPARK accuracy (linear model fitted
   on the calibration slice). Requests predicted easy are served by SPARK alone; the rest go to the GPU.
2) 3-tier cascade per byte: SPARK if its calibrated confidence >= t1; else the small GPU model if its own max
   probability >= t2; else the big GPU model. Thresholds chosen on cal (quality >= big model alone), reported on test.
Energy per byte-step: SPARK ~0; GPU models by parameter count (weight-read bound decode) -> toy (3.2M/4.8M) and the
projected 1B/7B pair."""
import json, os
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
C = 128


def feats(split):
    d = Z[f"{split}_text"]; sp = Z[f"{split}_sp"]; cf = Z[f"{split}_conf"]; pa = Z[f"{split}_path"]; bk = Z[f"{split}_bucket"]
    k = (len(d) - 1) // C; X, y, yb = [], [], []
    for i in range(k):
        s = slice(i * C, (i + 1) * C)
        c = cf[s]; b = bk[s]
        X.append([1, c.mean(), (c >= 0.9).mean(), (c >= 0.7).mean(), (pa[s] == 2).mean(), np.mean((b < 48) & (b // 12 == 3)),
                  np.mean(Z[f"{split}_small_pmax"][s])])
        y.append(np.mean(sp[s] == d[i * C + 1:(i + 1) * C + 1]))
        yb.append(np.mean(Z[f"{split}_big_pred"][s] == d[i * C + 1:(i + 1) * C + 1]))
    return np.array(X), np.array(y), np.array(yb)


Xc, yc, _ = feats("cal"); Xt, yt, ybt = feats("test")
w = np.linalg.lstsq(Xc, yc, rcond=None)[0]
pt = Xt @ w
rho = np.corrcoef(np.argsort(np.argsort(pt)), np.argsort(np.argsort(yt)))[0, 1]
rho0 = np.corrcoef(np.argsort(np.argsort(Xt[:, 1])), np.argsort(np.argsort(yt)))[0, 1]
print(f"REQUEST ROUTER: rank correlation with SPARK's real accuracy per request: trained {rho:.2f} (mean confidence only: {rho0:.2f})")
res = {"router": {"spearman_trained": float(rho), "spearman_meanconf": float(rho0), "points": []}}
order = np.argsort(-pt)
for f in (0.1, 0.2, 0.3, 0.5):
    e = order[:int(f * len(order))]
    print(f"  SPARK alone serves the easiest {f:.0%} of requests: SPARK {yt[e].mean():.1%} vs big GPU model {ybt[e].mean():.1%}")
    res["router"]["points"].append({"fraction": f, "spark_acc": float(yt[e].mean()), "big_acc": float(ybt[e].mean())})


def cascade(split, t1, t2):
    d = Z[f"{split}_text"][1:]; n = len(d)
    sp, cf = Z[f"{split}_sp"][:n], Z[f"{split}_conf"][:n]
    sm, smp, bg = Z[f"{split}_small_pred"][:n], Z[f"{split}_small_pmax"][:n], Z[f"{split}_big_pred"][:n]
    use_sp = cf >= t1; use_sm = (~use_sp) & (smp >= t2); use_bg = ~(use_sp | use_sm)
    out = np.where(use_sp, sp, np.where(use_sm, sm, bg))
    return {"acc": float(np.mean(out == d)), "spark": float(use_sp.mean()), "small_only": float(use_sm.mean()),
            "big": float(use_bg.mean()), "small_calls": float((~use_sp).mean())}


big_only = {s: float(np.mean(Z[f"{s}_big_pred"][:-1] == Z[f"{s}_text"][1:])) for s in ("cal", "test")}
grid = [(t1, t2) for t1 in (0.6, 0.7, 0.8, 0.9, 1.01) for t2 in (0.5, 0.6, 0.7, 0.8, 0.9, 1.01)]


def energy(r, small_P, big_P, two_tier=False):
    # every byte-step not answered by SPARK runs the small model first (it decides); unsure ones then run the big one
    return (0 if two_tier else r["small_calls"] * small_P) + r["big"] * big_P


print(f"\n3-TIER CASCADE (big GPU model alone: cal {big_only['cal']:.1%}, test {big_only['test']:.1%})")
res["cascade"] = []
for name, (sP, bP) in (("toy 3.2M/4.8M", (3.2, 4.8)), ("projected 1B/7B", (1.0, 7.0))):
    ok = [g for g in grid if cascade("cal", *g)["acc"] >= big_only["cal"] - 0.005]
    best = min(ok, key=lambda g: energy(cascade("cal", *g), sP, bP))
    r = cascade("test", *best); e = energy(r, sP, bP) / bP
    print(f"  {name}: SPARK {r['spark']:.0%}, small model {r['small_only']:.0%}, big model {r['big']:.0%} of byte-steps; "
          f"accuracy {r['acc']:.1%} vs big alone {big_only['test']:.1%}; GPU work {e:.0%} of big-alone ({1/e:.2f}x less)")
    # two-tier for comparison (no small model)
    ok2 = [g for g in grid if g[1] == 1.01 and cascade("cal", *g)["acc"] >= big_only["cal"] - 0.005]
    b2 = min(ok2, key=lambda g: energy(cascade("cal", *g), sP, bP, True)); r2 = cascade("test", *b2); e2 = energy(r2, sP, bP, True) / bP
    print(f"      2-tier (SPARK + big only): big model {r2['big']:.0%}; accuracy {r2['acc']:.1%}; GPU work {e2:.0%} ({1/e2:.2f}x less)")
    res["cascade"].append({"pair": name, "three_tier": {**r, "thresholds": best, "gpu_work": e}, "two_tier": {**r2, "thresholds": b2, "gpu_work": e2}})
json.dump(res, open(os.path.join(HERE, "..", "results", "router_v2.json"), "w"), indent=1)
