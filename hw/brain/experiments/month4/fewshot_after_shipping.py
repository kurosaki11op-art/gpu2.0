"""Few-shot after shipping: the chip already knows classes 0-4 (learned from all their examples, one stage), then meets
classes 5-9 with only k examples each (k = 1, 5, 20) as a second stage. Exact integer chip model, month-2 rule.
Network (MLP 784-256-10 on pixels, as in proof_suite_v3): (a) trained on 0-4, then fine-tuned on the k new examples
(continual, like the chip); (b) trained on 0-4 + the k new examples together (needs all old data kept: upper bound,
not continual). 3 seeds. Reports accuracy on old classes, new classes and all ten. usage: DATA_DIR DS"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np, torch
from cortex_core import load
from cortex_int import CortexInt
D, DS = sys.argv[1], sys.argv[2]
z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); ctr, cte = z["tr"], z["te"]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
xtr = xtr.reshape(len(xtr), -1) / 255.0; xte = xte.reshape(len(xte), -1) / 255.0
RULE = dict(B=10, night=2, daydream=1, night_stop=2)
old_te, new_te = yte < 5, yte >= 5


def mlp_fit(X, y, m=None, ep=5, seed=0, steps_min=0):
    torch.manual_seed(seed)
    m = m or torch.nn.Sequential(torch.nn.Linear(X.shape[1], 256), torch.nn.ReLU(), torch.nn.Linear(256, 10))
    opt = torch.optim.Adam(m.parameters(), 1e-3); Xt = torch.tensor(X, dtype=torch.float32); Yt = torch.tensor(y)
    g = torch.Generator().manual_seed(seed); ep = max(ep, int(np.ceil(steps_min * 64 / len(X))))
    for _ in range(ep):
        for b in torch.randperm(len(Xt), generator=g).split(64):
            opt.zero_grad(); torch.nn.functional.cross_entropy(m(Xt[b]), Yt[b]).backward(); opt.step()
    return m


def split(pred):
    return {"old": round(float((pred == yte)[old_te].mean()), 4), "new": round(float((pred == yte)[new_te].mean()), 4),
            "all": round(float((pred == yte).mean()), 4)}


res = {}
for k in (1, 5, 20):
    rows = {}
    for s in (1, 2, 3):
        g = np.random.RandomState(1000 * s)
        so = np.where(ytr < 5)[0]; so = so[g.permutation(len(so))]
        sn = np.concatenate([g.choice(np.where(ytr == c)[0], k, replace=False) for c in range(5, 10)]); sn = sn[g.permutation(len(sn))]
        m = CortexInt(ctr.shape[1], seed=s, **RULE); m.stage(ctr[so], ytr[so]); m.stage(ctr[sn], ytr[sn])
        rows.setdefault("chip", []).append(split(m.predict(cte)))
        net = mlp_fit(xtr[so], ytr[so], seed=s)
        ft = mlp_fit(xtr[sn], ytr[sn], m=net, ep=5, seed=s, steps_min=100)
        with torch.no_grad():
            rows.setdefault("network_finetuned", []).append(split(ft(torch.tensor(xte, dtype=torch.float32)).argmax(1).numpy()))
        both = np.concatenate([so, sn]); up = mlp_fit(xtr[both], ytr[both], seed=s)
        with torch.no_grad():
            rows.setdefault("network_all_data_kept", []).append(split(up(torch.tensor(xte, dtype=torch.float32)).argmax(1).numpy()))
    res[k] = {n: {key: round(float(np.mean([r[key] for r in v])), 4) for key in ("old", "new", "all")} for n, v in rows.items()}
    print(DS, "k", k, res[k], flush=True)
json.dump({"dataset": DS, "label": "SIMULATED (exact integer chip model; MLP baseline; 3 seeds)", "results": res},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f"fewshot_after_shipping_{DS}.json"), "w"), indent=1)
