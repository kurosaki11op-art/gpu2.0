"""SPARK Cortex proof suite: brain core vs a standard neural network (MLP, backprop) on the same data.

Brain core = sensory layer (feature_layer.Features: learns its own detectors without labels, winner-take-all,
Hebbian) + cortex memory (feature_layer.CountMemory: counts which features fire for which class; decides by
adding table scores). No multiplies in the chip, no backprop, no gradients.

Tests (each is a weakness of today's AI that a brain does not have):
  T1 accuracy, memory and operations per decision
  T2 few-shot     : 1 / 5 / 20 examples per class (cortex memory and episodic recall vs MLP)
  T3 continual    : 5 stages of 2 new classes; old data never shown again. Baselines: MLP fine-tuning, and
                    MLP with a replay buffer of 20 stored images per old class (a standard fix)
  T4 transfer     : two chips learn from different data; memories merged by adding counts (no retraining)
                    vs averaging two MLPs' weights
Sensory features are learned once, without labels, from stage-1 images only (classes 0 and 1), so no test
uses features that have seen later classes. Numbers SIMULATED on CPU; ops ESTIMATED.
usage: python proof_suite.py DATA_DIR [mnist|fashion]"""
import json, os, sys, time
import numpy as np, torch
from cortex_core import load
from feature_layer import Features, CountMemory, PS

D, DS = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "mnist"
F = 128
torch.manual_seed(0); np.random.seed(0)
xtr, ytr, xte, yte = load(D, DS)
ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
t0 = time.time()
fe = Features(F).fit(xtr[np.isin(ytr, stages[0])][:12000])
enc = lambda x: np.concatenate([fe.encode(x[i:i + 5000]) for i in range(0, len(x), 5000)])
ctr, cte = enc(xtr), enc(xte)
NB = ctr.shape[1]


def c_acc(m, idx=None):
    i = slice(None) if idx is None else idx
    return float((m.predict(cte[i]) == yte[i]).mean())


class MLP(torch.nn.Module):
    def __init__(s, seed=0):
        super().__init__(); torch.manual_seed(seed)
        s.f = torch.nn.Sequential(torch.nn.Linear(784, 256), torch.nn.ReLU(), torch.nn.Linear(256, 10))

    def forward(s, x):
        return s.f(x)


def mlp(x, y, seed=0, ep=5, m=None, steps_min=0):
    m = m or MLP(seed); opt = torch.optim.Adam(m.parameters(), 1e-3)
    X, Y = torch.tensor(x, dtype=torch.float32) / 255, torch.tensor(y)
    g = torch.Generator().manual_seed(seed)
    ep = max(ep, int(np.ceil(steps_min * 64 / len(x))))
    for _ in range(ep):
        for idx in torch.randperm(len(X), generator=g).split(64):
            opt.zero_grad(); torch.nn.functional.cross_entropy(m(X[idx]), Y[idx]).backward(); opt.step()
    return m


def m_acc(m, idx=None):
    i = slice(None) if idx is None else idx
    with torch.no_grad():
        return float((m(torch.tensor(xte[i], dtype=torch.float32) / 255).argmax(1).numpy() == yte[i]).mean())


R = {"dataset": DS, "features": F, "feature_bits": NB, "label": "SIMULATED (ops ESTIMATED)"}
# T1 ---------------------------------------------------------------------------------------------------
c = CountMemory(NB, 10).learn(ctr, ytr); n = mlp(xtr, ytr)
npos = ((28 - PS) // 2 + 1) ** 2
R["T1"] = {"cortex_acc": c_acc(c), "mlp_acc": m_acc(n),
           "cortex_memory_KB": {"feature_detectors": F * PS * PS / 8 / 1024, "class_table_8bit": NB * 10 / 1024},
           "mlp_memory_KB_8bit": sum(p.numel() for p in n.parameters()) / 1024,
           "cortex_ops_per_decision": {"25bit_match_popcounts": npos * F, "table_adds": int(ctr.sum(1).mean()) * 10,
                                       "multiplies": 0},
           "mlp_ops_per_decision": {"multiply_adds": 784 * 256 + 256 * 10},
           "cortex_learning": "features: 3 unlabeled passes over stage-1 patches; class memory: 1 pass, counting only",
           "mlp_learning": "5 passes of backprop"}
print("T1", R["T1"]["cortex_acc"], R["T1"]["mlp_acc"], f"{time.time()-t0:.0f}s", flush=True)
# T2 few-shot -----------------------------------------------------------------------------------------
R["T2"] = {}
for k in (1, 5, 20):
    ca, ea, ma = [], [], []
    for s in range(3):
        r = np.random.RandomState(s)
        idx = np.concatenate([r.choice(np.where(ytr == c_)[0], k, replace=False) for c_ in range(10)])
        ca.append(float((CountMemory(NB, 10).learn(ctr[idx], ytr[idx]).predict(cte) == yte).mean()))
        ov = cte.astype(np.int32) @ ctr[idx].astype(np.int32).T          # AND + popcount overlap (episodic recall)
        ea.append(float((ytr[idx][ov.argmax(1)] == yte).mean()))
        ma.append(m_acc(mlp(xtr[idx], ytr[idx], seed=s, ep=50, steps_min=300)))
    R["T2"][f"{k}_per_class"] = {"cortex_memory": float(np.mean(ca)), "episodic_recall": float(np.mean(ea)), "mlp": float(np.mean(ma))}
    print("T2", k, R["T2"][f"{k}_per_class"], flush=True)
# T3 continual ----------------------------------------------------------------------------------------
c3, n3, r3, buf, hist = CountMemory(NB, 10), None, None, [], []
for i, st in enumerate(stages):
    sel = np.where(np.isin(ytr, st))[0]
    c3.learn(ctr[sel], ytr[sel])
    n3 = mlp(xtr[sel], ytr[sel], m=n3, ep=2)
    rsel = np.concatenate([sel] + buf)                                     # replay: new data + stored old images
    r3 = mlp(xtr[rsel], ytr[rsel], m=r3, ep=2)
    rs = np.random.RandomState(i)
    buf += [rs.choice(np.where(ytr == c_)[0], 20, replace=False) for c_ in st]
    seen = np.isin(yte, sum(stages[:i + 1], ())); first = np.isin(yte, stages[0])
    hist.append({"stage": i + 1,
                 "cortex_all_seen": c_acc(c3, seen), "mlp_all_seen": m_acc(n3, seen), "mlp_replay_all_seen": m_acc(r3, seen),
                 "cortex_stage1": c_acc(c3, first), "mlp_stage1": m_acc(n3, first), "mlp_replay_stage1": m_acc(r3, first)})
    print("T3", {k: round(v, 4) for k, v in hist[-1].items()}, flush=True)
R["T3"] = hist
R["T3_note"] = "cortex keeps no stored images; mlp_replay keeps 20 raw images per old class"
# T4 transfer -----------------------------------------------------------------------------------------
h = len(xtr) // 2
cA, cB = CountMemory(NB, 10).learn(ctr[:h], ytr[:h]), CountMemory(NB, 10).learn(ctr[h:], ytr[h:])
nA, nB = mlp(xtr[:h], ytr[:h], seed=0), mlp(xtr[h:], ytr[h:], seed=1)
avg = MLP(); avg.load_state_dict({k: (nA.state_dict()[k] + nB.state_dict()[k]) / 2 for k in nA.state_dict()})
sA, sB = ytr < 5, ytr >= 5
kA, kB = CountMemory(NB, 10).learn(ctr[sA], ytr[sA]), CountMemory(NB, 10).learn(ctr[sB], ytr[sB])
qA, qB = mlp(xtr[sA], ytr[sA]), mlp(xtr[sB], ytr[sB], seed=1)
qavg = MLP(); qavg.load_state_dict({k: (qA.state_dict()[k] + qB.state_dict()[k]) / 2 for k in qA.state_dict()})
R["T4"] = {"same_classes_different_data": {"cortex_A": c_acc(cA), "cortex_B": c_acc(cB), "cortex_merged": c_acc(cA.merge(cB)),
                                           "cortex_trained_on_all": c_acc(c),
                                           "mlp_A": m_acc(nA), "mlp_B": m_acc(nB), "mlp_weight_average": m_acc(avg)},
           "different_classes": {"cortex_A_0to4": c_acc(kA), "cortex_B_5to9": c_acc(kB), "cortex_merged": c_acc(kA.merge(kB)),
                                 "mlp_A": m_acc(qA), "mlp_B": m_acc(qB), "mlp_weight_average": m_acc(qavg)}}
print("T4", json.dumps(R["T4"]), flush=True)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", f"cortex_proof_{DS}.json")
json.dump(R, open(out, "w"), indent=1)
print(f"done {time.time()-t0:.0f}s")
