#!/usr/bin/env python3
"""Redesign test 4 (31 Oct 2026): a prototype layer learned without labels plus a closed-form readout, at full data. Bars: new_start/step19_k4_plan.md (written before the run).
usage: python k4_prototype_layer.py [--tasks fashion,mnist] [--k 3000] [--seeds 2] [--out results/k4_results.json]"""
import argparse, json, os, sys, time
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "k2")); sys.path.insert(0, os.path.join(HERE, "..", "k1"))
import k2_strong_baselines as k2  # noqa
import k1_data_efficiency as k1  # noqa
torch.set_num_threads(4); PASSES = 3; E_BIT, E_MAC = k1.E_BIT, k1.E_MAC

def kmeans(Xu, K, seed):
    g = torch.Generator().manual_seed(seed); C = Xu[torch.randperm(len(Xu), generator=g)[:K]].clone()
    for _ in range(PASSES):
        a = torch.cat([((Xu[i:i + 6000] @ C.T) - 0.5 * (C * C).sum(1)[None]).argmax(1) for i in range(0, len(Xu), 6000)])
        Cn = torch.zeros_like(C); Cn.index_add_(0, a, Xu); cnt = torch.bincount(a, minlength=K).float(); empty = cnt == 0
        Cn = Cn / cnt.clamp(min=1)[:, None]; Cn[empty] = Xu[torch.randint(0, len(Xu), (int(empty.sum()),), generator=g)]; C = Cn
    return C

def feats(X, C, mu=None, sd=None):
    F = torch.cat([(X[i:i + 6000] @ C.T) - 0.5 * (C * C).sum(1)[None] for i in range(0, len(X), 6000)])
    if mu is None: mu, sd = F.mean(0), F.std(0).clamp(min=1e-6)
    return (F - mu) / sd, mu, sd

def ridge_fit(Z, Y, lam):
    ym = Y.mean(0); zm = Z.mean(0); Zc = Z - zm; G = Zc.T @ Zc + lam * torch.eye(Z.shape[1]); W = torch.linalg.solve(G, Zc.T @ (Y - ym)); return W, ym - zm @ W

def quant(W, bits):
    q = 2 ** (bits - 1) - 1; s = W.abs().max(0).values.clamp(min=1e-9) / q; return torch.round(W / s).clamp(-q, q) * s

def best_lam(Z, Y, lams=(1.0, 10.0, 100.0, 1000.0, 10000.0)):
    n = len(Z); p = torch.randperm(n, generator=torch.Generator().manual_seed(7)); vi, ti = p[: n // 10], p[n // 10:]; best = None
    for lam in lams:
        W, b = ridge_fit(Z[ti], Y[ti], lam); acc = float(((Z[vi] @ W + b).argmax(1) == Y[vi].argmax(1)).float().mean())
        if best is None or acc > best[0]: best = (acc, lam)
    return best[1]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tasks", default="fashion,mnist"); ap.add_argument("--k", type=int, default=3000); ap.add_argument("--seeds", type=int, default=2); ap.add_argument("--out", default="results/k4_results.json"); a = ap.parse_args(); res = {}
    for task in a.tasks.split(","):
        xtr, ytr, xte, yte, ctr, cte = k2.task_data(task); Xu = torch.tensor(ctr, dtype=torch.float32); Xt = torch.tensor(cte, dtype=torch.float32); Y = torch.nn.functional.one_hot(torch.tensor(ytr), 10).float(); yt = torch.tensor(yte); out = {}
        t0 = time.time(); lam1 = best_lam(Xu, Y); W, b = ridge_fit(Xu, Y, lam1); out["R1_code_ridge"] = float(((Xt @ W + b).argmax(1) == yt).float().mean()); print(f"[{task}] R1 ridge on the code (lambda {lam1}): {out['R1_code_ridge']:.4f}  ({time.time()-t0:.0f}s)", flush=True)
        for name, K in (("R2", 1000), ("R3", a.k)):
            accs, q8, q5 = [], [], []
            for s in range(a.seeds):
                t0 = time.time(); C = kmeans(Xu, K, 500 + s); Z, mu, sd = feats(Xu, C); Zt, _, _ = feats(Xt, C, mu, sd); lam = best_lam(Z, Y); W, b = ridge_fit(Z, Y, lam)
                accs.append(float(((Zt @ W + b).argmax(1) == yt).float().mean())); q8.append(float(((Zt @ quant(W, 8) + b).argmax(1) == yt).float().mean())); q5.append(float(((Zt @ quant(W, 5) + b).argmax(1) == yt).float().mean()))
                print(f"[{task}] {name} K={K} seed {s}: float {accs[-1]:.4f}  int8 readout {q8[-1]:.4f}  5-bit readout {q5[-1]:.4f}  (lambda {lam}, {time.time()-t0:.0f}s)", flush=True)
            out[name] = dict(K=K, float=float(np.mean(accs)), int8=float(np.mean(q8)), bit5=float(np.mean(q5)), seeds=accs)
        n_tr = len(ctr); inf_bitops = a.k * ctr.shape[1]; inf_nJ = (inf_bitops * E_BIT + a.k * 10 * E_MAC) * 1e-3
        train_J = (12000 * 2 * k1.ENC_BITOPS * E_BIT + n_tr * k1.ENC_BITOPS * E_BIT + PASSES * n_tr * a.k * ctr.shape[1] * E_BIT) * 1e-12 * 28 + (n_tr * a.k * a.k + 5 * a.k ** 3) * E_MAC * 1e-12
        out["inference_nJ_per_image"] = inf_nJ; out["training_energy_J"] = train_J; res[task] = out; print(f"[{task}] counted inference {inf_nJ:.1f} nJ per image; counted training {train_J:.3f} J", flush=True); json.dump(res, open(a.out, "w"), indent=1)
    f, m = res.get("fashion"), res.get("mnist")
    ka = f and f["R3"]["float"] >= 0.90; kb = m and m["R3"]["float"] >= 0.989; kc = f and f["inference_nJ_per_image"] <= 1000.0; kd = f and f["training_energy_J"] <= 2.5 / 5; ke = f and m and (f["R3"]["float"] - f["R3"]["int8"] <= 0.005) and (m["R3"]["float"] - m["R3"]["int8"] <= 0.005)
    print(f"BARS: K4-a clothing >= 90.0%: {'PASS' if ka else 'FAIL'} ({f['R3']['float']*100:.2f});  K4-b digits >= 98.9%: {'PASS' if kb else 'FAIL'} ({m['R3']['float']*100:.2f});  K4-c inference <= 1.0 uJ: {'PASS' if kc else 'FAIL'} ({f['inference_nJ_per_image']:.0f} nJ);  K4-d training <= 0.5 J: {'PASS' if kd else 'FAIL'} ({f['training_energy_J']:.2f} J);  K4-e int8 loss <= 0.5 pt: {'PASS' if ke else 'FAIL'}" if f and m else "BARS: need both tasks")

if __name__ == "__main__":
    main()
