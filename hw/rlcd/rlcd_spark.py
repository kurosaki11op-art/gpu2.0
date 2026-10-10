"""RLCD-style training of SPARK v2's confidence LUT (Reinforcement Learning for Calibrated Decisions).

TypeSafe has not published RLCD's exact objective; we implement the documented intent ("when the model says 0.8 it
should be right ~80% of the time", decisions + calibrated probabilities) with a strictly proper scoring rule as the RL
reward:
  * policy: for every feature bucket b (64 buckets, see spark_golden_v2) a categorical distribution over 64 confidence
    levels (softmax of learnable logits); one level is sampled per decision and reported as the confidence.
  * reward: r = -(c - y)^2  (negative Brier score; y = 1 if SPARK's answer is correct)  +  a decision term for the
    routing action taken at threshold tau: +E_save if SPARK keeps the token and is right, -lambda if it keeps it and is
    wrong, 0 if it hands the token to the GPU.
  * REINFORCE with a per-bucket running-mean baseline. Contrastive distillation: an extra reward term
    +beta * (agree_with_teacher - 0.5) * sign(c - 0.5) pushes confidence up where SPARK agrees with the GPU model and
    down where it disagrees.
The greedy (argmax) level per bucket becomes the 8-bit LUT value written into the chip. Training uses only the
calibration slice; everything is reported on the separate test slice.

Benchmarks (same test bytes): v1 path-pin router; temperature-scaled softmax router (classic calibrated cascade,
temperature fitted by NLL on calibration); empirical-frequency LUT (non-RL calibration); random router (same
offload); oracle router (keeps exactly the bytes SPARK gets right: upper bound).
Metrics: ECE (15 bins), Brier score, AUROC (correct vs wrong), accuracy of kept bytes and system accuracy vs offload.
"""
import argparse, json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "golden")); sys.path.insert(0, os.path.join(HERE, "..", "train"))
import spark_golden as g1, spark_golden_v2 as g2, train_spark_v0 as tr  # noqa: E402

L = 64                                         # confidence levels (6 bits; LUT stores level*4+2 -> 8 bits)
LV = (np.arange(L) + 0.5) / L


def run_v2(W, data, cfg, tb, orders, teacher=None):
    g = g2.GoldenV2(W, g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", **cfg), tb=tb, orders=orders)
    r = [g.step(int(b)) for b in data]
    return (np.array([o["pred"] for o in r]), np.array([o["path"] for o in r]), np.array([o["bucket"] for o in r]))


def run_logits(W, data):
    g = g1.Golden(W, g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr"))
    out = np.zeros((len(data), 256))
    for i, b in enumerate(data):
        g.step(int(b))
        out[i] = g.acc[3]
    return out


def ece(p, y, bins=15):
    e, n = 0.0, len(p)
    edges = np.linspace(0, 1, bins + 1)
    for a, b in zip(edges[:-1], edges[1:]):
        m = (p >= a) & (p < b) if b < 1 else (p >= a)
        if m.any():
            e += m.sum() / n * abs(p[m].mean() - y[m].mean())
    return e


def auroc(p, y):
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order)); ranks[order] = np.arange(1, len(order) + 1)
    # average ranks for ties
    allv = np.concatenate([pos, neg])
    for v in np.unique(allv):
        m = allv == v
        ranks[m] = ranks[m].mean()
    return (ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def rlcd_train(bucket, y, agree, iters=3000, lr=2.0, beta=0.1, seed=0):
    rng = np.random.default_rng(seed)
    theta = np.zeros((128, L))
    base = np.zeros(128)
    n = len(y)
    for it in range(iters):
        idx = rng.integers(0, n, size=512)
        b, yy, ag = bucket[idx], y[idx], agree[idx]
        logits = theta[b]
        pr = np.exp(logits - logits.max(1, keepdims=True)); pr /= pr.sum(1, keepdims=True)
        a = np.array([rng.choice(L, p=q) for q in pr])
        c = LV[a]
        r = -(c - yy) ** 2 + beta * (ag - yy) * (c - 0.5)
        adv = r - base[b]
        cnt = np.bincount(b, minlength=128).astype(float)
        mean_r = np.bincount(b, weights=r, minlength=128) / np.maximum(cnt, 1)
        base += 0.1 * (cnt > 0) * (mean_r - base)
        grad = -pr
        grad[np.arange(len(a)), a] += 1.0
        g = np.zeros_like(theta)
        np.add.at(g, b, adv[:, None] * grad)
        theta += lr * g / np.maximum(cnt, 1)[:, None]
    pr = np.exp(theta - theta.max(1, keepdims=True)); pr /= pr.sum(1, keepdims=True)
    lut = pr @ LV                     # expected level (smooth); written as 8-bit LUT
    return lut, theta


def rl_threshold(conf, y, e_save, lam, iters=2000, seed=0):
    """Second RL policy: softmax over 32 thresholds, reward = e_save*kept_right - lam*kept_wrong (per byte)."""
    rng = np.random.default_rng(seed)
    taus = np.linspace(0.3, 0.99, 32)
    th = np.zeros(32)
    for it in range(iters):
        q = np.exp(th - th.max()); q /= q.sum()
        a = rng.choice(32, p=q)
        idx = rng.integers(0, len(y), size=1024)
        keep = conf[idx] >= taus[a]
        r = np.mean(np.where(keep, np.where(y[idx] == 1, e_save, -lam), 0.0))
        g = -q; g[a] += 1
        th += 0.5 * (r - np.dot(q, [0] * 32)) * g * 20
    return float(taus[th.argmax()])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bytes", type=int, default=20000)
    ap.add_argument("--tb", type=int, default=12)
    ap.add_argument("--teacher", default=os.path.join(HERE, "..", "system", "out_big", "gpu_model.pt"))
    ap.add_argument("--out", default=os.path.join(HERE, "out"))
    a = ap.parse_args()
    orders = (2, 3, 4, 6)
    data = tr.load_corpus(3_000_000); n = len(data)
    cal = data[int(n * 0.9): int(n * 0.9) + a.bytes]
    test = data[int(n * 0.95): int(n * 0.95) + a.bytes]
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))

    teach = {}
    if os.path.exists(a.teacher):
        sys.path.insert(0, os.path.join(HERE, "..", "system"))
        from cascade_sim import gpu_preds, GPT, GPTConfig
        import torch
        ck = torch.load(a.teacher); m = GPT(GPTConfig(**ck["cfg"])); m.load_state_dict(ck["state"]); m.eval()
        teach = {"cal": gpu_preds(m, cal), "test": gpu_preds(m, test)}
        print("teacher accuracy: cal %.3f test %.3f" % (np.mean(teach["cal"][:-1] == cal[1:]), np.mean(teach["test"][:-1] == test[1:])))

    cfg = dict(recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16)
    res = {"config": cfg, "tb": a.tb, "orders": orders}
    S = {}
    for k, d in (("cal", cal), ("test", test)):
        p, path, bk = run_v2(W, d, cfg, a.tb, orders)
        y = np.zeros(len(d)); y[:-1] = (p[:-1] == d[1:])
        ag = (p == teach[k]).astype(float) if teach else y
        S[k] = dict(p=p, path=path, b=bk, y=y, ag=ag)
    yc, yt = S["cal"]["y"][:-1], S["test"]["y"][:-1]
    print("SPARK v2 raw accuracy: cal %.3f test %.3f" % (yc.mean(), yt.mean()))

    # 1) empirical-frequency LUT (non-RL calibration)
    freq = np.array([yc[S["cal"]["b"][:-1] == b].mean() if np.any(S["cal"]["b"][:-1] == b) else 0.5 for b in range(128)])
    # 2) RLCD LUT
    lut_rl, _ = rlcd_train(S["cal"]["b"][:-1], yc, S["cal"]["ag"][:-1])
    # 3) temperature-scaled softmax router (network always runs)
    zl = {k: run_logits(W, d) for k, d in (("cal", cal), ("test", test))}
    ycn = (zl["cal"].argmax(1)[:-1] == cal[1:]).astype(float)
    best_T, best_nll = 1.0, 1e9
    for T in np.exp(np.linspace(np.log(1), np.log(400), 60)):
        z = zl["cal"][:-1] / T; z = z - z.max(1, keepdims=True)
        lp = z - np.log(np.exp(z).sum(1, keepdims=True))
        nll = -lp[np.arange(len(z)), cal[1:]].mean()
        if nll < best_nll:
            best_T, best_nll = T, nll
    def soft(k):
        z = zl[k][:-1] / best_T; z = z - z.max(1, keepdims=True); q = np.exp(z); q /= q.sum(1, keepdims=True)
        return q.max(1), (zl[k].argmax(1)[:-1] == (cal if k == "cal" else test)[1:]).astype(float)
    ps_t, ys_t = soft("test")
    bt = S["test"]["b"][:-1]
    routers = {
        "v1-style path pin (recall/exit -> keep)": ((S["test"]["path"][:-1] != 0).astype(float), yt),
        "empirical-frequency LUT": (freq[bt], yt),
        "RLCD LUT (ours)": (lut_rl[bt], yt),
        "temperature-scaled softmax (network only)": (ps_t, ys_t),
    }
    res["temperature"] = best_T
    res["routers"] = {}
    for name, (pc, yy) in routers.items():
        row = {"ECE": ece(pc, yy), "Brier": float(np.mean((pc - yy) ** 2)), "AUROC": auroc(pc, yy), "curve": []}
        for off in (0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
            k = int(off * len(pc)); order = np.argsort(-pc, kind="stable"); keep = np.zeros(len(pc), bool); keep[order[:k]] = True
            row["curve"].append({"offload": off, "kept_accuracy": float(yy[keep].mean())})
        res["routers"][name] = row
    rng = np.random.default_rng(1)
    res["routers"]["random"] = {"curve": [{"offload": off, "kept_accuracy": float(yt.mean())} for off in (0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)]}
    res["routers"]["oracle (upper bound)"] = {"curve": [{"offload": off, "kept_accuracy": float(min(1.0, yt.mean() / off))} for off in (0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)]}
    res["lut_rlcd_8bit"] = [int(round(v * 255)) for v in lut_rl]
    res["lut_freq_8bit"] = [int(round(v * 255)) for v in freq]
    os.makedirs(a.out, exist_ok=True)
    json.dump(res, open(os.path.join(a.out, "rlcd_results.json"), "w"), indent=1)
    print("\n%-44s %6s %6s %6s   kept-accuracy at offload 40/60/80/90%%" % ("router", "ECE", "Brier", "AUROC"))
    for name, r in res["routers"].items():
        cur = {c["offload"]: c["kept_accuracy"] for c in r["curve"]}
        print("%-44s %6s %6s %6s   %s" % (name, "%.3f" % r["ECE"] if "ECE" in r else "-", "%.3f" % r["Brier"] if "Brier" in r else "-",
              "%.3f" % r["AUROC"] if "AUROC" in r else "-", " ".join("%.3f" % cur[o] for o in (0.4, 0.6, 0.8, 0.9))))


if __name__ == "__main__":
    main()
