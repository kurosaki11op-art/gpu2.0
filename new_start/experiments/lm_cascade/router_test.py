#!/usr/bin/env python3
"""Diagnosis and learned router for the small-plus-large language cascade (31 Oct 2026). Bars and plan: new_start/step9_router_plan.md (written before the run).
Teacher-forced, one pass of each model over each slice; features from the SMALL model only (so a router costs nothing extra at run time).
Usage: python router_test.py --small NAME --big NAME [--device cpu] [--train 20000] [--test 10220] [--val 5000] [--out results/router.json]"""
import argparse, json
import numpy as np, torch
from transformers import AutoModelForCausalLM, AutoTokenizer

@torch.no_grad()
def collect(small, big, ids, win, device):
    """per position: lp_s, lp_b (log-prob of the true next token), small-model scalar features, small last hidden state."""
    lp_s, lp_b, sc, hid = [], [], [], []
    for i in range(0, ids.numel() - win, win):
        x = ids[i:i + win].unsqueeze(0).to(device)
        o = small(x[:, :-1], output_hidden_states=True); ls = torch.log_softmax(o.logits[0].float(), -1); h = o.hidden_states[-1][0].float()
        lb = torch.log_softmax(big(x[:, :-1]).logits[0].float(), -1); y = x[0, 1:].unsqueeze(1)
        p = ls.exp(); t5 = p.topk(5, -1).values; ent = -(p * ls).sum(-1)
        lp_s.append(ls.gather(1, y).squeeze(1).cpu()); lp_b.append(lb.gather(1, y).squeeze(1).cpu())
        sc.append(torch.stack([t5[:, 0] - t5[:, 1], t5[:, 0], ent, t5.sum(-1), torch.log(t5[:, 0] - t5[:, 1] + 1e-6)], 1).cpu()); hid.append(h.cpu())
    return torch.cat(lp_s).numpy(), torch.cat(lp_b).numpy(), torch.cat(sc).numpy(), torch.cat(hid).numpy()

def ridge_fit(X, y, alpha):
    mu, sd = X.mean(0), X.std(0) + 1e-6; Z = (X - mu) / sd; ym = y.mean()
    w = np.linalg.solve(Z.T @ Z + alpha * np.eye(Z.shape[1]), Z.T @ (y - ym)); return lambda Xn: ((Xn - mu) / sd) @ w + ym

def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b)); return float(np.corrcoef(ra, rb)[0, 1])

def curve(lp_s, lp_b, score, rs, rng):
    """cascade NLL when escalating the top-r positions by score (higher = escalate first); gap closed; random control."""
    n = lp_s.size; nll_s, nll_b = -lp_s.mean(), -lp_b.mean(); den = nll_s - nll_b; order = np.argsort(-score); rows = []
    for r in rs:
        k = int(round(r * n)); e = np.zeros(n, bool); e[order[:k]] = True; nll = -np.where(e, lp_b, lp_s).mean()
        rnd = np.mean([-np.where(np.isin(np.arange(n), rng.choice(n, k, replace=False)), lp_b, lp_s).mean() for _ in range(3)])
        rows.append(dict(r=r, nll=float(nll), ratio=float(nll / nll_b), gap=float((nll_s - nll) / den), gap_random=float((nll_s - rnd) / den)))
    return rows

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--small", required=True); ap.add_argument("--big", required=True); ap.add_argument("--device", default="cpu")
    ap.add_argument("--train", type=int, default=20000); ap.add_argument("--test", type=int, default=10220); ap.add_argument("--val", type=int, default=5000); ap.add_argument("--win", type=int, default=512)
    ap.add_argument("--out", default="results/router.json"); a = ap.parse_args()
    from datasets import load_dataset
    tok = AutoTokenizer.from_pretrained(a.small); assert tok.get_vocab() == AutoTokenizer.from_pretrained(a.big).get_vocab()
    def ids_of(split, n, skip=0):
        t = "\n\n".join(load_dataset("Salesforce/wikitext", "wikitext-2-raw-v1", split=split)["text"]); x = tok(t, return_tensors="pt").input_ids[0]; return x[skip:skip + n + 1]
    dt = torch.float32
    small = AutoModelForCausalLM.from_pretrained(a.small, dtype=dt).to(a.device).eval(); big = AutoModelForCausalLM.from_pretrained(a.big, dtype=dt).to(a.device).eval()
    sl = {"train": ids_of("train", a.train, 50000), "test": ids_of("test", a.test), "val": ids_of("validation", a.val)}; D = {k: collect(small, big, v, a.win, a.device) for k, v in sl.items()}
    print({k: int(v[0].size) for k, v in D.items()}, flush=True)
    # ---- Part 1: diagnosis on the test slice
    lp_s, lp_b, sc, hid = D["test"]; gain = lp_b - lp_s; marg = sc[:, 0]; n = gain.size; low = np.argsort(marg)[: int(0.3 * n)]
    diag = dict(spearman_margin_gain=spearman(marg, gain), mean_gain=float(gain.mean()), share_low30_gain_under_005=float((gain[low] < 0.05).mean()), mean_gain_low30=float(gain[low].mean()),
                mean_gain_rest=float(np.delete(gain, low).mean()), decile_gain=[float(gain[np.argsort(marg)][i * n // 10:(i + 1) * n // 10].mean()) for i in range(10)])
    diag["hypothesis_supported"] = bool(abs(diag["spearman_margin_gain"]) < 0.3 and diag["share_low30_gain_under_005"] >= 0.25)
    print("DIAGNOSIS (test slice):", json.dumps(diag, indent=1), flush=True)
    # ---- Part 2: routers
    Xs = {k: np.concatenate([v[2], v[2][:, :1] ** 0 * 0 + v[2][:, 2:3] ** 2], 1) for k, v in D.items()}; XB = {k: np.concatenate([Xs[k], D[k][3]], 1) for k in D}
    ytr = D["train"][1] - D["train"][0]; m = int(0.8 * ytr.size); res = {}
    def fit(X, name):
        best = None
        for alpha in [1.0, 10.0, 100.0, 1000.0, 10000.0]:
            f = ridge_fit(X["train"][:m], ytr[:m], alpha); err = float(np.mean((f(X["train"][m:]) - ytr[m:]) ** 2))
            if best is None or err < best[0]: best = (err, alpha)
        f = ridge_fit(X["train"], ytr, best[1]); print(f"router {name}: alpha {best[1]}, held-out MSE {best[0]:.4f} (train variance {float(ytr.var()):.4f})", flush=True); return f, best[1]
    fA, aA = fit(Xs, "A (scalar)"); fB, aB = fit(XB, "B (scalar + hidden)")
    rs = [0.10, 0.20, 0.30, 0.40, 0.50]; rng = np.random.default_rng(0)
    for k in ("test", "val"):
        ls, lb = D[k][0], D[k][1]
        res[k] = dict(nll_small=float(-ls.mean()), nll_big=float(-lb.mean()), margin=curve(ls, lb, -D[k][2][:, 0], rs, rng), routerA=curve(ls, lb, fA(Xs[k]), rs, rng), routerB=curve(ls, lb, fB(XB[k]), rs, rng),
                      oracle=curve(ls, lb, lb - ls, rs, rng))
        print(f"\n[{k}] tokens {ls.size}  nll small {res[k]['nll_small']:.4f}  big {res[k]['nll_big']:.4f}")
        print(f"{'esc':>5} | {'margin x big':>12} {'gap':>6} | {'router A x big':>14} {'gap':>6} | {'router B x big':>14} {'gap':>6} | {'random gap':>10} | {'oracle gap':>10}")
        for i, r in enumerate(rs):
            mg, ra, rb, orc = res[k]["margin"][i], res[k]["routerA"][i], res[k]["routerB"][i], res[k]["oracle"][i]
            print(f"{r:>5.2f} | {mg['ratio']:>12.3f} {mg['gap']:>6.3f} | {ra['ratio']:>14.3f} {ra['gap']:>6.3f} | {rb['ratio']:>14.3f} {rb['gap']:>6.3f} | {mg['gap_random']:>10.3f} | {orc['gap']:>10.3f}", flush=True)
    bars = {}
    for k in ("test", "val"):
        i30 = rs.index(0.30); mg, rb = res[k]["margin"], res[k]["routerB"]
        bars[k] = dict(R1=bool(rb[i30]["ratio"] <= 1.01), R2=bool(rb[i30]["gap"] >= 2 * mg[i30]["gap"]), R3=bool(all(rb[i]["gap"] > mg[i]["gap"] for i in range(len(rs)))))
    print("\nBARS (router B):", json.dumps(bars)); res["diagnosis"] = diag; res["bars"] = bars; json.dump(res, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
