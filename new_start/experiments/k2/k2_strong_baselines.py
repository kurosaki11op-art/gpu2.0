#!/usr/bin/env python3
"""Row K test 2 (31 Oct 2026): L Cortex counting recipe against tuned and simple baselines, 5 seeds at small N, two tasks (Fashion-MNIST, MNIST), conservative energy accounting.
Bars: new_start/step17_k2_plan.md (written before the run). usage: python k2_strong_baselines.py [--ns 100,300,1000,3000,10000,60000] [--tasks fashion,mnist] [--out results.json]"""
import argparse, json, os, sys, time
import numpy as np, torch, torch.nn.functional as F
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "k1"))
import k1_data_efficiency as k1  # noqa  (also puts hw/brain on the path)
from cortex_core import load  # noqa
from cortex_slow import CortexSlow  # noqa
from feature_layer import Features  # noqa
torch.set_num_threads(4); LAYOUT = 28.0; E_MAC, E_ADD, E_BIT = k1.E_MAC, k1.E_ADD, k1.E_BIT

def task_data(task):
    xtr, ytr, xte, yte = load(k1.D, task); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
    if task == "fashion": ctr, cte = k1.codes(xtr, ytr, xte)
    else:
        p = "/tmp/k2_mnist_codes.npz"
        if os.path.exists(p): z = np.load(p); ctr, cte = z["ctr"], z["cte"]
        else:
            CH = (50, 150, ("on", 8), ("off", 8)); fes = [Features(32, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
            enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)]).astype(np.uint8)
            ctr, cte = enc(xtr), enc(xte); np.savez(p, ctr=ctr, cte=cte)
    return xtr, ytr, xte, yte, ctr, cte

def cnn_tuned(xs, ys, xte, yte, seed, flip, bs=64):
    """tuned small CNN: lr from {1e-3, 3e-3} by a held-out 10%, weight decay 1e-4, shift (and flip) augmentation, at least 600 steps; returns test acc, epochs summed over both lr runs, MACs summed over both."""
    g = np.random.RandomState(seed); n = len(xs); p = g.permutation(n); nv = max(10, n // 10); vi, ti = p[:nv], p[nv:]
    X = torch.tensor(xs.reshape(-1, 1, 28, 28) / 255.0, dtype=torch.float32); Y = torch.tensor(ys); Xt = torch.tensor(xte.reshape(-1, 1, 28, 28) / 255.0, dtype=torch.float32)
    spe = max(1, -(-len(ti) // bs)); max_ep = min(200, max(15, -(-600 // spe))); patience = max(3, -(-150 // spe)); best_all = None; macs = 0.0
    for lr in (1e-3, 3e-3):
        torch.manual_seed(seed); net = k1.Net(); opt = torch.optim.Adam(net.parameters(), lr, weight_decay=1e-4); best, bst, bad, eps = -1, None, 0, 0
        for ep in range(max_ep):
            net.train(); o = g.permutation(ti)
            for i in range(0, len(o), bs):
                b = o[i:i + bs]; xb = X[b]; dy, dx = g.randint(-2, 3, 2); xb = torch.roll(xb, (int(dy), int(dx)), (2, 3))
                if flip: m = torch.tensor(g.rand(len(b)) < 0.5); xb = torch.where(m[:, None, None, None], xb.flip(3), xb)
                opt.zero_grad(); F.cross_entropy(net(xb), Y[b]).backward(); opt.step()
            eps += 1; net.eval()
            with torch.no_grad(): va = (net(X[vi]).argmax(1) == Y[vi]).float().mean().item()
            if va > best: best, bst, bad = va, {k: v.clone() for k, v in net.state_dict().items()}, 0
            else:
                bad += 1
                if bad >= patience: break
        macs += eps * len(ti) * 3 * k1.CNN_FWD_MAC + eps * nv * k1.CNN_FWD_MAC
        if best_all is None or best > best_all[0]: net.load_state_dict(bst); net.eval(); best_all = (best, {k: v.clone() for k, v in net.state_dict().items()})
    net = k1.Net(); net.load_state_dict(best_all[1]); net.eval()
    with torch.no_grad(): acc = float(np.mean([(net(Xt[i:i + 2000]).argmax(1).numpy() == yte[i:i + 2000]).mean() for i in range(0, len(Xt), 2000)]))
    return acc, macs

def knn(xs, ys, xte, yte, seed):
    g = np.random.RandomState(seed); n = len(xs); p = g.permutation(n); nv = max(10, n // 10); vi, ti = p[:nv], p[nv:]
    A = torch.tensor(xs / 255.0, dtype=torch.float32); Y = torch.tensor(ys); Q = torch.tensor(xte / 255.0, dtype=torch.float32)
    def pred(Xr, Yr, Xq, k):
        out = []
        for i in range(0, len(Xq), 1000):
            d = torch.cdist(Xq[i:i + 1000], Xr); idx = d.topk(min(k, len(Xr)), largest=False).indices; v = Yr[idx]
            out.append(torch.mode(v, 1).values if k > 1 else v[:, 0])
        return torch.cat(out)
    bk = max((1, 3, 5), key=lambda k: float((pred(A[ti], Y[ti], A[vi], k) == Y[vi]).float().mean()))
    return float((pred(A, Y, Q, bk).numpy() == yte).mean())

def linear(xs, ys, xte, yte, seed):
    torch.manual_seed(seed); A = torch.tensor(xs / 255.0, dtype=torch.float32); Y = torch.tensor(ys); Q = torch.tensor(xte / 255.0, dtype=torch.float32)
    W = torch.nn.Linear(784, 10); opt = torch.optim.Adam(W.parameters(), 1e-2, weight_decay=1e-4); n = len(A)
    steps = 300 if n <= 10000 else 1200
    for s in range(steps):
        b = torch.randint(0, n, (min(n, 2048),)); opt.zero_grad(); F.cross_entropy(W(A[b]), Y[b]).backward(); opt.step()
    return float((W(Q).argmax(1).numpy() == yte).mean())

def randfeat(xs, ys, xte, yte, seed, D=4096):
    g = torch.Generator().manual_seed(seed); R = torch.randn(784, D, generator=g) / 28.0; b = torch.randn(D, generator=g)
    A = torch.tensor(xs / 255.0, dtype=torch.float32); Q = torch.tensor(xte / 255.0, dtype=torch.float32); Y1 = F.one_hot(torch.tensor(ys), 10).float() - 0.1
    Z = lambda X: F.relu(X @ R + b); n = len(A); p = torch.randperm(n, generator=g); nv = max(10, n // 10); vi, ti = p[:nv], p[nv:]
    def fit(idx, lam): Zi = Z(A[idx]); return torch.linalg.solve(Zi.T @ Zi + lam * torch.eye(D), Zi.T @ Y1[idx])
    bl = max((1.0, 100.0, 1e4), key=lambda lam: float(((Z(A[vi]) @ fit(ti, lam)).argmax(1) == torch.tensor(ys)[vi]).float().mean()))
    return float(((Z(Q) @ fit(torch.arange(n), bl)).argmax(1).numpy() == yte).mean())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ns", default="100,300,1000,3000,10000,60000"); ap.add_argument("--tasks", default="fashion,mnist"); ap.add_argument("--out", default="results/k2_results.json"); a = ap.parse_args()
    res = {}
    for task in a.tasks.split(","):
        xtr, ytr, xte, yte, ctr, cte = task_data(task); na = float(ctr[:5000].sum(1).mean()); ex_pj = 26 * na * E_ADD; enc_pj = k1.ENC_BITOPS * E_BIT; fit_pj = 12000 * 2 * k1.ENC_BITOPS * E_BIT; rows = []
        for N in [int(v) for v in a.ns.split(",")]:
            ns = 5 if N <= 3000 else (3 if N == 10000 else 1); acc = {k: [] for k in ("L", "cnn", "knn", "linear", "randfeat")}; macs = []; tL = tC = 0.0
            for s in range(ns):
                sub = np.random.RandomState(100 + s).permutation(len(ytr))[:N]; xs, ys = xtr[sub], ytr[sub]
                t0 = time.time(); m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1 + s); m.stage(ctr[sub], ys); S = m.S.T.astype(np.int32)
                acc["L"].append(float(((cte.astype(np.int32) @ S).argmax(1) == yte).mean())); tL += time.time() - t0
                t0 = time.time(); c, mc = cnn_tuned(xs, ys, xte, yte, s, task == "fashion"); acc["cnn"].append(c); macs.append(mc); tC += time.time() - t0
                acc["knn"].append(knn(xs, ys, xte, yte, s)); acc["linear"].append(linear(xs, ys, xte, yte, s)); acc["randfeat"].append(randfeat(xs, ys, xte, yte, s))
            mean = {k: float(np.mean(v)) for k, v in acc.items()}; std = {k: float(np.std(v)) for k, v in acc.items()}; best = max((k for k in acc if k != "L"), key=lambda k: mean[k])
            eL = (fit_pj + N * (enc_pj + ex_pj)) * 1e-12 * LAYOUT; eC = float(np.mean(macs)) * E_MAC * 1e-12
            row = dict(N=N, seeds=ns, mean=mean, std=std, best_baseline=best, energy_L_conservative_J=eL, energy_cnn_J=eC, ratio=eC / eL, wall_L_s=tL / ns, wall_cnn_s=tC / ns); rows.append(row)
            print(f"[{task}] N={N:>6} ({ns} seeds)  L {mean['L']:.4f}+-{std['L']:.4f} | CNN {mean['cnn']:.4f}+-{std['cnn']:.4f} | kNN {mean['knn']:.4f} | linear {mean['linear']:.4f} | randfeat {mean['randfeat']:.4f} | best baseline {best}  | energy ratio (L x{LAYOUT:.0f}) {eC/eL:.0f}x  wall L {tL/ns:.0f}s CNN {tC/ns:.0f}s", flush=True)
            res[task] = rows; json.dump(res, open(a.out, "w"), indent=1)
    def gap(task, N): r = next((x for x in res.get(task, []) if x["N"] == N), None); return None if r is None else r["mean"]["L"] - r["mean"][r["best_baseline"]]
    fa = res.get("fashion", []); ka = all(gap("fashion", n) is not None and gap("fashion", n) >= -0.01 for n in (1000, 3000))
    both = [r for r in fa if r["mean"]["L"] >= 0.85 and r["mean"]["cnn"] >= 0.85]; kb = bool(both) and both[-1]["ratio"] >= 20
    kc = gap("fashion", 60000) is not None and gap("fashion", 60000) >= -0.03
    kd = gap("mnist", 1000) is not None and gap("mnist", 1000) >= -0.01 and gap("mnist", 60000) is not None and gap("mnist", 60000) >= -0.03
    g = lambda t, n: "n/a" if gap(t, n) is None else f"{gap(t, n)*100:+.2f}"
    print(f"BARS: K2-a {'PASS' if ka else 'FAIL'} (L minus best baseline, points: fashion 1,000 {g('fashion',1000)}, 3,000 {g('fashion',3000)}; need >= -1);  K2-b {'PASS' if kb else 'FAIL'} (ratio {both[-1]['ratio']:.0f}x at N={both[-1]['N']} with L x{LAYOUT:.0f}; need >= 20);  K2-c {'PASS' if kc else 'FAIL'} (60,000: {g('fashion',60000)}; need >= -3);  K2-d {'PASS' if kd else 'FAIL'} (mnist 1,000 {g('mnist',1000)}, 60,000 {g('mnist',60000)})" if both else "BARS: no N with both >= 85%")

if __name__ == "__main__":
    main()
