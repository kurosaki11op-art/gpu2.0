#!/usr/bin/env python3
"""Row K test 3 (31 Oct 2026): few-label methods on L's 4,608-bit code that use the unlabelled training images. Bars: new_start/step18_k3_plan.md (written before the run).
usage: python k3_few_labels.py [--ns 100,300,1000] [--tasks fashion,mnist] [--seeds 5] [--out results/k3_results.json]"""
import argparse, json, os, sys, time
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "k2")); sys.path.insert(0, os.path.join(HERE, "..", "k1"))
import k2_strong_baselines as k2  # noqa
import k1_data_efficiency as k1  # noqa
from cortex_slow import CortexSlow  # noqa
torch.set_num_threads(4); K = 300; PASSES = 3; LAYOUT = 28.0; E_BIT = k1.E_BIT

def kmeans(Xu, seed):
    """3 Lloyd passes on the unlabelled codes (float matrix), K prototypes initialised from random images."""
    g = torch.Generator().manual_seed(seed); C = Xu[torch.randperm(len(Xu), generator=g)[:K]].clone()
    for _ in range(PASSES):
        d = (Xu @ C.T) - 0.5 * (C * C).sum(1)[None, :]; a = d.argmax(1)
        Cn = torch.zeros_like(C); Cn.index_add_(0, a, Xu); cnt = torch.bincount(a, minlength=K).float()
        empty = cnt == 0; Cn = Cn / cnt.clamp(min=1)[:, None]; Cn[empty] = Xu[torch.randint(0, len(Xu), (int(empty.sum()),), generator=g)]; C = Cn
    return C

def ridge_loo(Z, Y, lams=(0.01, 0.1, 1.0, 10.0, 100.0, 1000.0, 10000.0)):
    """ridge with intercept; the penalty is chosen by exact leave-one-out squared error; returns (weights, bias)."""
    mu, ym = Z.mean(0), Y.mean(0); Zc, Yc = Z - mu, Y - ym; U, S, Vt = torch.linalg.svd(Zc, full_matrices=False); UtY = U.T @ Yc; best = None
    for lam in lams:
        f = S ** 2 / (S ** 2 + lam); yh = U @ (f[:, None] * UtY); h = (U ** 2 * f[None, :]).sum(1); loo = float((((Yc - yh) / (1 - h).clamp(min=1e-3)[:, None]) ** 2).mean())
        if best is None or loo < best[0]: best = (loo, lam)
    lam = best[1]; W = Vt.T @ ((S / (S ** 2 + lam))[:, None] * UtY); return W, ym - mu @ W

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ns", default="100,300,1000"); ap.add_argument("--tasks", default="fashion,mnist"); ap.add_argument("--seeds", type=int, default=5); ap.add_argument("--out", default="results/k3_results.json"); a = ap.parse_args()
    res = {}
    for task in a.tasks.split(","):
        xtr, ytr, xte, yte, ctr, cte = k2.task_data(task); Xu = torch.tensor(ctr, dtype=torch.float32); Xt = torch.tensor(cte, dtype=torch.float32)
        centers = {}; t0 = time.time()
        for s in range(a.seeds): centers[s] = kmeans(Xu, 1000 + s)
        print(f"[{task}] k-means ({K} clusters, {PASSES} passes) x {a.seeds} seeds: {time.time()-t0:.0f}s", flush=True)
        # counted energy of the unlabelled part: encoding 60,000 images and the clustering passes (bit operations), times the layout factor
        e_unl = (len(ctr) * k1.ENC_BITOPS + PASSES * len(ctr) * K * ctr.shape[1]) * E_BIT * 1e-12 * LAYOUT; rows = []
        for N in [int(v) for v in a.ns.split(",")]:
            acc = {m: [] for m in ("M0", "M1", "M2", "M3a", "M3b")}
            for s in range(a.seeds):
                sub = np.random.RandomState(100 + s).permutation(len(ytr))[:N]; Xl = Xu[sub]; Y = torch.nn.functional.one_hot(torch.tensor(ytr[sub]), 10).float() - 0.1; ys = torch.tensor(ytr[sub]); yt = torch.tensor(yte)
                m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1 + s); m.stage(ctr[sub], ytr[sub]); S0 = torch.tensor(m.S.T.astype(np.float32)); acc["M0"].append(float(((Xt @ S0).argmax(1) == yt).float().mean()))
                mu = torch.stack([Xl[ys == c].mean(0) if (ys == c).any() else torch.zeros(Xl.shape[1]) for c in range(10)]); acc["M1"].append(float((((Xt @ mu.T) - 0.5 * (mu * mu).sum(1)[None]).argmax(1) == yt).float().mean()))
                W, b = ridge_loo(Xl, Y); acc["M2"].append(float(((Xt @ W + b).argmax(1) == yt).float().mean()))
                C = centers[s]; fl = (Xl @ C.T) - 0.5 * (C * C).sum(1)[None]; al = fl.argmax(1); lab = torch.full((K,), -1, dtype=torch.long)
                for k in range(K):
                    v = ys[al == k]
                    if len(v): lab[k] = torch.bincount(v, minlength=10).argmax()
                named = torch.where(lab >= 0)[0]; d = (C[:, None, :] - C[None, named, :]).pow(2).sum(2) if False else None
                dc = (C @ C[named].T) - 0.5 * (C[named] * C[named]).sum(1)[None]; near = named[dc.argmax(1)]; lab = torch.where(lab >= 0, lab, lab[near])
                at = ((Xt @ C.T) - 0.5 * (C * C).sum(1)[None]).argmax(1); acc["M3a"].append(float((lab[at] == yt).float().mean()))
                Ft = (Xt @ C.T) - 0.5 * (C * C).sum(1)[None]; fmu, fsd = Fu_stats(Xu, C); Zl = (fl - fmu) / fsd; Zt = (Ft - fmu) / fsd; W3, b3 = ridge_loo(Zl, Y); acc["M3b"].append(float(((Zt @ W3 + b3).argmax(1) == yt).float().mean()))
            mean = {k: float(np.mean(v)) for k, v in acc.items()}; std = {k: float(np.std(v)) for k, v in acc.items()}
            eL = (12000 * 2 * k1.ENC_BITOPS * E_BIT * 1e-12 * LAYOUT) + e_unl + N * k1.ENC_BITOPS * E_BIT * 1e-12 * LAYOUT
            rows.append(dict(N=N, mean=mean, std=std, energy_M3b_J=eL)); print(f"[{task}] N={N:>5}  M0 {mean['M0']:.4f} | M1 {mean['M1']:.4f} | M2 {mean['M2']:.4f} | M3a {mean['M3a']:.4f} | M3b {mean['M3b']:.4f}+-{std['M3b']:.4f} | counted energy M3b {eL*1e3:.1f} mJ", flush=True)
        res[task] = rows; json.dump(res, open(a.out, "w"), indent=1)

def Fu_stats(Xu, C):
    """mean and std of the cluster similarities over the unlabelled images (computed in chunks)."""
    s1 = torch.zeros(len(C)); s2 = torch.zeros(len(C)); base = 0.5 * (C * C).sum(1)[None]
    for i in range(0, len(Xu), 10000): f = (Xu[i:i + 10000] @ C.T) - base; s1 += f.sum(0); s2 += (f * f).sum(0)
    mu = s1 / len(Xu); return mu, ((s2 / len(Xu) - mu ** 2).clamp(min=1e-6)).sqrt()

if __name__ == "__main__":
    main()
