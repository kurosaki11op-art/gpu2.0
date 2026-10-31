#!/usr/bin/env python3
"""Row K test 1 (31 Oct 2026): accuracy and training compute against the number of labelled examples, L Cortex counting recipe vs a small CNN trained by gradient descent (labelled baseline).
Bars: new_start/step16_k1_plan.md (written before the run). usage: python k1_data_efficiency.py [--ns 100,300,1000,3000,10000,60000] [--out results.json]
Env: K1_DATA (Fashion-MNIST gz folder, default /tmp/fashion), K1_CACHE (npz cache of the 4,608-bit codes)."""
import argparse, json, os, sys, time
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F
HB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "hw", "brain"); sys.path.insert(0, HB)
from cortex_core import load  # noqa
from cortex_slow import CortexSlow  # noqa
import feature_layer; feature_layer.PS, feature_layer.ST = 5, 1  # noqa
from feature_layer import Features  # noqa
torch.set_num_threads(4)
D = os.environ.get("K1_DATA", "/tmp/fashion"); CACHE = os.environ.get("K1_CACHE", "/tmp/k1_codes.npz")
SCR = "/tmp/claude-0/-home-user-gpu2-0/320c8e52-5b63-5218-8e07-5330166bbbbd/scratchpad/shirt_cache.npz"
# assumed energies (pJ): 16-bit multiply-add (project value), 8-bit add, XNOR plus bit count per bit
E_MAC, E_ADD, E_BIT = 1.5, 0.03, 0.003
ENC_BITOPS = 576 * 128 * 25      # positions x templates x bits of the fixed encoder, per image
CNN_FWD_MAC = 26 * 26 * 16 * 9 + 11 * 11 * 32 * 16 * 9 + 800 * 10

def codes(xtr, ytr, xte):
    p = SCR if os.path.exists(SCR) else CACHE
    if os.path.exists(p):
        z = np.load(p); return z["ctr"], z["cte"]
    CH = (50, 150, ("on", 8), ("off", 8)); fes = [Features(32, thr=c, pool=4).fit(xtr[np.isin(ytr, (0, 1))][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 5000]) for g in fes], 1) for i in range(0, len(x), 5000)]).astype(np.uint8)
    ctr, cte = enc(xtr), enc(xte); np.savez(CACHE, ctr=ctr, cte=cte); return ctr, cte

class Net(nn.Module):
    def __init__(s): super().__init__(); s.c1 = nn.Conv2d(1, 16, 3); s.c2 = nn.Conv2d(16, 32, 3); s.fc = nn.Linear(800, 10)
    def forward(s, x): x = F.max_pool2d(F.relu(s.c1(x)), 2); x = F.max_pool2d(F.relu(s.c2(x)), 2); return s.fc(x.flatten(1))

def run_cnn(xs, ys, xte, yte, seed, max_ep=15, patience=3, bs=64):
    torch.manual_seed(seed); g = np.random.RandomState(seed); n = len(xs); p = g.permutation(n); nv = max(10, n // 10); vi, ti = p[:nv], p[nv:]
    spe = max(1, -(-len(ti) // bs))                      # gradient steps per epoch; a dry run showed 30 steps (N=100) is too few, so every run gets at least 600 steps and patience of at least 150 steps
    max_ep = min(200, max(max_ep, -(-600 // spe))); patience = max(patience, -(-150 // spe))
    X = torch.tensor(xs.reshape(-1, 1, 28, 28) / 255.0, dtype=torch.float32); Y = torch.tensor(ys); Xt = torch.tensor(xte.reshape(-1, 1, 28, 28) / 255.0, dtype=torch.float32)
    net = Net(); opt = torch.optim.Adam(net.parameters(), 1e-3); best, bstate, bad, ep_run = -1, None, 0, 0
    for ep in range(max_ep):
        net.train(); o = g.permutation(ti)
        for i in range(0, len(o), bs):
            b = o[i:i + bs]; opt.zero_grad(); F.cross_entropy(net(X[b]), Y[b]).backward(); opt.step()
        ep_run += 1; net.eval()
        with torch.no_grad(): va = (net(X[vi]).argmax(1) == Y[vi]).float().mean().item()
        if va > best: best, bstate, bad = va, {k: v.clone() for k, v in net.state_dict().items()}, 0
        else:
            bad += 1
            if bad >= patience: break
    net.load_state_dict(bstate); net.eval()
    with torch.no_grad(): acc = float(np.mean([(net(Xt[i:i + 2000]).argmax(1).numpy() == yte[i:i + 2000]).mean() for i in range(0, len(Xt), 2000)]))
    macs = ep_run * len(ti) * 3 * CNN_FWD_MAC + ep_run * nv * CNN_FWD_MAC
    return acc, ep_run, macs

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ns", default="100,300,1000,3000,10000,60000"); ap.add_argument("--out", default="k1_results.json"); a = ap.parse_args()
    xtr, ytr, xte, yte = load(D, "fashion"); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); ctr, cte = codes(xtr, ytr, xte)
    na = float(ctr[:5000].sum(1).mean()); adds_per_ex = 26 * na
    fit_pj = 12000 * 2 * ENC_BITOPS * E_BIT; enc_pj = ENC_BITOPS * E_BIT; ex_pj = adds_per_ex * E_ADD
    print(f"mean active code bits {na:.0f}; L per example: encoder {ENC_BITOPS*E_BIT/1e6:.3f} uJ, learning {adds_per_ex} adds = {ex_pj/1e6:.5f} uJ; fixed encoder fitting {fit_pj/1e6:.1f} uJ", flush=True)
    rows = []
    for N in [int(v) for v in a.ns.split(",")]:
        sub = np.random.RandomState(100).permutation(len(ytr))[:N]; t0 = time.time()
        m = CortexSlow(ctr.shape[1], ch=500, K=5, night_stop=2, daydream=1, seed=1); m.stage(ctr[sub], ytr[sub]); S = m.S.T.astype(np.int32); accL = float(((cte.astype(np.int32) @ S).argmax(1) == yte).mean()); tL = time.time() - t0
        eL = (fit_pj + N * (enc_pj + ex_pj)) * 1e-12
        seeds = [0, 1] if N <= 3000 else [0]; t0 = time.time(); res = [run_cnn(xtr[sub], ytr[sub], xte, yte, s) for s in seeds]; tC = time.time() - t0
        accC = float(np.mean([r[0] for r in res])); eps = float(np.mean([r[1] for r in res])); macs = float(np.mean([r[2] for r in res])); eC = macs * E_MAC * 1e-12
        rows.append(dict(N=N, acc_L=accL, acc_cnn=accC, cnn_seed_accs=[r[0] for r in res], cnn_epochs=eps, cnn_macs=macs, energy_L_J=eL, energy_cnn_J=eC, ratio_energy=eC / eL, wall_L_s=tL, wall_cnn_s=tC))
        print(f"N={N:>6}  L {accL:.4f}  CNN {accC:.4f} (seeds {[round(r[0],4) for r in res]}, {eps:.1f} epochs)  energy L {eL*1e6:.1f} uJ, CNN {eC*1e6:.1f} uJ, ratio {eC/eL:.0f}x   wall L {tL:.0f}s CNN {tC:.0f}s", flush=True)
        json.dump(dict(rows=rows, mean_active_bits=na, adds_per_example=adds_per_ex), open(a.out, "w"), indent=1)
    r = {x["N"]: x for x in rows}
    ka = all(r[n]["acc_L"] >= r[n]["acc_cnn"] - 0.01 for n in (1000, 3000) if n in r)
    both = [x for x in rows if x["acc_L"] >= 0.85 and x["acc_cnn"] >= 0.85]; kb = bool(both) and both[-1]["ratio_energy"] >= 20
    kc = 60000 in r and r[60000]["acc_L"] >= r[60000]["acc_cnn"] - 0.03
    print(f"BARS: K1-a (L >= CNN - 1pt at 1,000 and 3,000) {'PASS' if ka else 'FAIL'};  K1-b (energy ratio >= 20x at largest N with both >= 85%: N={both[-1]['N'] if both else None}) {'PASS' if kb else 'FAIL'};  K1-c (60,000: within 3 pts) {'PASS' if kc else 'FAIL'}")

if __name__ == "__main__":
    main()
