#!/usr/bin/env python3
"""Redesign test 5 (31 Oct 2026): a hidden layer on L's 4,608-bit code. Bars: new_start/step20_k5_plan.md (written before the run).
usage: python k5_hidden_layer.py [--tasks fashion,mnist] [--seeds 2] [--epochs 25] [--out results/k5_results.json]"""
import argparse, json, os, sys, time
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "k2")); sys.path.insert(0, os.path.join(HERE, "..", "k1"))
import k2_strong_baselines as k2  # noqa
import k1_data_efficiency as k1  # noqa
torch.set_num_threads(4); E_ADD8, E_MAC8, E_BIT = 0.03, 0.25, k1.E_BIT

def make(hs): 
    layers, d = [], 4608
    for h in hs: layers += [nn.Linear(d, h), nn.ReLU(), nn.Dropout(0.2)]; d = h
    return nn.Sequential(*layers, nn.Linear(d, 10))

def train(Xtr, ytr, hs, epochs, seed, bs=256):
    torch.manual_seed(seed); net = make(hs); opt = torch.optim.Adam(net.parameters(), 1e-3); n = len(Xtr)
    for ep in range(epochs):
        net.train(); p = torch.randperm(n)
        for i in range(0, n, bs):
            b = p[i:i + bs]; opt.zero_grad(); F.cross_entropy(net(Xtr[b]), ytr[b]).backward(); opt.step()
    return net

def acc(net, X, y):
    net.eval()
    with torch.no_grad(): return float(np.mean([(net(X[i:i + 5000]).argmax(1) == y[i:i + 5000]).float().mean().item() for i in range(0, len(X), 5000)]))

def best_epochs(Xtr, ytr, hs, epochs, seed, bs=256):
    n = len(Xtr); p = torch.randperm(n, generator=torch.Generator().manual_seed(seed)); vi, ti = p[: n // 10], p[n // 10:]; torch.manual_seed(seed); net = make(hs); opt = torch.optim.Adam(net.parameters(), 1e-3); best = (-1, 1)
    for ep in range(epochs):
        net.train(); q = ti[torch.randperm(len(ti))]
        for i in range(0, len(q), bs):
            b = q[i:i + bs]; opt.zero_grad(); F.cross_entropy(net(Xtr[b]), ytr[b]).backward(); opt.step()
        a = acc(net, Xtr[vi], ytr[vi])
        if a > best[0]: best = (a, ep + 1)
    return best[1]

def quant_(net, bits=8):
    q = 2 ** (bits - 1) - 1
    with torch.no_grad():
        for m in net:
            if isinstance(m, nn.Linear): s = m.weight.abs().max().clamp(min=1e-9) / q; m.weight.copy_(torch.round(m.weight / s).clamp(-q, q) * s)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tasks", default="fashion,mnist"); ap.add_argument("--seeds", type=int, default=2); ap.add_argument("--epochs", type=int, default=25); ap.add_argument("--out", default="results/k5_results.json"); a = ap.parse_args(); res = {}
    for task in a.tasks.split(","):
        xtr, ytr, xte, yte, ctr, cte = k2.task_data(task); Xtr = torch.tensor(ctr, dtype=torch.float32); Xte = torch.tensor(cte, dtype=torch.float32); Y = torch.tensor(ytr); Yt = torch.tensor(yte); out = {}
        for name, hs in (("main_256", (256,)), ("abl_1024", (1024,)), ("abl_512_256", (512, 256))):
            accs, q8s, t0 = [], [], time.time()
            for s in range(a.seeds if name == "main_256" else 1):
                ep = best_epochs(Xtr, Y, hs, a.epochs, s); net = train(Xtr, Y, hs, ep, s); accs.append(acc(net, Xte, Yt)); quant_(net, 8); q8s.append(acc(net, Xte, Yt))
                print(f"[{task}] {name} seed {s}: float {accs[-1]:.4f}  int8 weights {q8s[-1]:.4f}  (epochs {ep}, {time.time()-t0:.0f}s)", flush=True)
            out[name] = dict(float=float(np.mean(accs)), int8=float(np.mean(q8s)), seeds=accs)
        na = float(ctr[:5000].sum(1).mean()); h = 256
        inf_J = (k1.ENC_BITOPS * E_BIT + na * h * E_ADD8 + h * 10 * E_MAC8) * 1e-12; macs_train = 3 * (4608 * h + h * 10) * len(ctr) * (a.epochs * 1.1) ; train_J = macs_train * 1.5e-12 + 12000 * 2 * k1.ENC_BITOPS * E_BIT * 1e-12 + len(ctr) * k1.ENC_BITOPS * E_BIT * 1e-12
        out["inference_nJ_raw"] = inf_J * 1e9; out["inference_nJ_layout28"] = inf_J * 28e9; out["training_J_counted"] = train_J; res[task] = out; print(f"[{task}] counted inference {inf_J*1e9:.1f} nJ raw, {inf_J*28e9:.0f} nJ with the layout factor; counted training {train_J:.2f} J", flush=True); json.dump(res, open(a.out, "w"), indent=1)
    f, m = res.get("fashion"), res.get("mnist")
    if f and m:
        ka = f["main_256"]["float"] >= 0.905; kb = m["main_256"]["float"] >= 0.989; kc = (f["main_256"]["float"] - f["main_256"]["int8"] <= 0.003) and (m["main_256"]["float"] - m["main_256"]["int8"] <= 0.003); kd = f["inference_nJ_layout28"] <= 1000; ke = f["training_J_counted"] <= 5 * 2.5
        print(f"BARS: K5-a clothing >= 90.5%: {'PASS' if ka else 'FAIL'} ({f['main_256']['float']*100:.2f});  K5-b digits >= 98.9%: {'PASS' if kb else 'FAIL'} ({m['main_256']['float']*100:.2f});  K5-c int8 loss <= 0.3 pt: {'PASS' if kc else 'FAIL'} (clothing {100*(f['main_256']['float']-f['main_256']['int8']):.2f}, digits {100*(m['main_256']['float']-m['main_256']['int8']):.2f});  K5-d inference <= 1.0 uJ (x28): {'PASS' if kd else 'FAIL'} ({f['inference_nJ_layout28']:.0f} nJ);  K5-e training <= 12.5 J: {'PASS' if ke else 'FAIL'} ({f['training_J_counted']:.1f} J)")

if __name__ == "__main__":
    main()
