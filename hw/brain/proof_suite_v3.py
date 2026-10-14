"""SPARK Cortex month-2 suite (v3): small memory, one decision rule for every task.

Design under test (same rule for digits, clothing and spoken words):
  senses + sensory layer : as month 1, but 32 detectors per channel (images, 4,608-bit code) / 64 (sound, 23,040)
  decision               : the fast table only (5-bit signed counters), always
  dream memory           : DREAM=rate   per-class 8-bit firing rates, metaplastic learning (rate_memory.RateMemory)
                           DREAM=count  per-class exact counters (16-bit), naive dreams (feature_layer.CountMemory)
                           DREAM=online single-pass concept cells, exact 16-bit counters (rate_memory.OnlineConcepts)
  sleep                  : day = practise new examples + dreams of old classes;
                           NIGHT=1 adds a night of dreams of all known classes (2 passes)
Tests: all at once, 5 stages, merge of two chips (classes 0-4 / 5-9), few-shot (1/5/20 per class).
Baselines: MLP 784-256-10 (sound: also FFT log-mel); in stages: fine-tuning and replay of 20 stored examples/class.
SIMULATED. usage: DREAM=rate|count|online NIGHT=0|1 python proof_suite_v3.py DATA_DIR mnist|fashion|speech"""
import json, os, sys, time
import numpy as np, torch
from cortex_core import load
from feature_layer import Features, CountMemory
from rate_memory import RateMemory, OnlineConcepts
from sleep import SurpriseTable, dreams as count_dreams

D, DS = sys.argv[1], sys.argv[2]
DREAM, NIGHT = os.environ.get("DREAM", "rate"), int(os.environ.get("NIGHT", "1"))
CMAX, NDREAM = 15, 6000
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
torch.manual_seed(0); np.random.seed(0); t0 = time.time()
if DS == "speech":
    import cochlea
    xtr, ytr, xte, yte = cochlea.load_speech(os.path.join(D, "speech"), os.path.join(D, "speech_pics_res.npz"),
                                             cochlea.sound_picture_res)
    btr, _, bte, _ = cochlea.log_mel(os.path.join(D, "speech"), os.path.join(D, "speech_mel.npz"))
    base = {"pictures": (xtr / 255.0, xte / 255.0), "log-mel": (btr, bte)}
    CH, F = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8)), 64
else:
    xtr, ytr, xte, yte = load(D, DS)
    base = {"pixels": (xtr / 255.0, xte / 255.0)}
    CH, F = (50, 150, ("on", 8), ("off", 8)), 32
ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
cache = os.path.join(D, f"sep_{DS}_F{F}_p2.npz")
if os.path.exists(cache):
    z = np.load(cache); ctr, cte = z["tr"], z["te"]
else:
    fes = [Features(F, thr=c).fit(xtr[np.isin(ytr, stages[0])][:12000]) for c in CH]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
    ctr, cte = enc(xtr), enc(xte); np.savez_compressed(cache, tr=ctr, te=cte)
NB = ctr.shape[1]
print(DS, DREAM, "night", NIGHT, "code", ctr.shape, f"{time.time()-t0:.0f}s", flush=True)


def new_mem(seed=0):
    return {"rate": lambda: RateMemory(NB, 10, B=8, k=0, kmax=9, seed=seed), "count": lambda: CountMemory(NB, 10),
            "online": lambda: OnlineConcepts(NB, 10, P=8, seed=seed)}[DREAM]()


def dream(mem, classes, n, seed):
    return count_dreams(mem, classes, n, seed=seed) if DREAM == "count" else mem.dreams(classes, n, seed)


def acc(st, idx, known):
    return float((st.predict(cte[idx], known) == yte[idx]).mean())


def brain(idx_stages, seed=0, mem=None, st=None, known=None):
    mem = mem or new_mem(seed); st = st or SurpriseTable(NB, 10, cmax=CMAX)
    known = np.zeros(10, bool) if known is None else known; hist = []
    for i, sel in enumerate(idx_stages):
        mem.learn(ctr[sel], ytr[sel]); old = np.where(known)[0]; known[np.unique(ytr[sel])] = True
        X, Y = ctr[sel], ytr[sel]
        if len(old):
            dx, dy = dream(mem, old, NDREAM, seed * 10 + i); X = np.concatenate([X, dx]); Y = np.concatenate([Y, dy])
        st.practise(X, Y, known, seed=seed * 10 + i)
        if NIGHT and len(old):
            dx, dy = dream(mem, np.where(known)[0], NDREAM, 100 + seed * 10 + i); st.practise(dx, dy, known, epochs=2, seed=100 + i)
        hist.append(acc(st, np.isin(yte, np.where(known)[0]), known))
    return mem, st, known, hist


def mlp_fit(X, y, m=None, ep=5, seed=0, steps_min=0):
    m = m or torch.nn.Sequential(torch.nn.Linear(X.shape[1], 256), torch.nn.ReLU(), torch.nn.Linear(256, 10))
    opt = torch.optim.Adam(m.parameters(), 1e-3); Xt = torch.tensor(X, dtype=torch.float32); Yt = torch.tensor(y)
    g = torch.Generator().manual_seed(seed); ep = max(ep, int(np.ceil(steps_min * 64 / len(X))))
    for _ in range(ep):
        for b in torch.randperm(len(Xt), generator=g).split(64):
            opt.zero_grad(); torch.nn.functional.cross_entropy(m(Xt[b]), Yt[b]).backward(); opt.step()
    return m


def mlp_acc(m, X, y):
    with torch.no_grad():
        return float((m(torch.tensor(X, dtype=torch.float32)).argmax(1).numpy() == y).mean())


R = {"dataset": DS, "label": "SIMULATED", "dream_memory": DREAM, "night": NIGHT, "code_bits": NB, "table_bits": 5}
allk = np.ones(10, bool); every = np.ones(len(yte), bool)
st_all = SurpriseTable(NB, 10, cmax=CMAX).practise(ctr, ytr, allk)
R["all_at_once"] = {"brain_table": acc(st_all, every, allk)}
for k, (b1, b2) in base.items():
    R["all_at_once"][f"mlp_{k}"] = mlp_acc(mlp_fit(b1, ytr), b2, yte)
print("all at once", R["all_at_once"], flush=True)
sidx = [np.where(np.isin(ytr, s))[0] for s in stages]
_, _, _, R["stages_brain"] = brain(sidx)
for k, (b1, b2) in base.items():
    m = r = None; buf = []; h = []
    for i, sel in enumerate(sidx):
        m = mlp_fit(b1[sel], ytr[sel], m, ep=2); rs = np.concatenate([sel] + buf); r = mlp_fit(b1[rs], ytr[rs], r, ep=2)
        buf += [np.random.RandomState(i).choice(np.where(ytr == c)[0], 20, replace=False) for c in stages[i]]
        seen = np.isin(yte, sum(stages[:i + 1], ()))
        h.append({"mlp": mlp_acc(m, b2[seen], yte[seen]), "mlp_replay20": mlp_acc(r, b2[seen], yte[seen])})
    R[f"stages_mlp_{k}"] = h
print("stages brain", np.round(R["stages_brain"], 4), {k: R[k][-1] for k in R if k.startswith("stages_mlp")}, flush=True)
# merge: chip A learns 0-4, chip B 5-9 (each in one stage); merge = add tables and dream memories, then one night
iA, iB = np.where(ytr < 5)[0], np.where(ytr >= 5)[0]
mA, sA, kA, _ = brain([iA], seed=1); mB, sB, kB, _ = brain([iB], seed=2)
if DREAM == "rate":
    mM = new_mem(); mM.r = np.where(np.arange(10)[:, None] < 5, mA.r, mB.r); mM.seen = mA.seen + mB.seen
elif DREAM == "count":
    mM = mA.merge(mB)
else:
    mM = new_mem(); mM.on = mA.on + mB.on; mM.n = mA.n + mB.n
sM = SurpriseTable(NB, 10, cmax=CMAX); sM.W = np.clip(sA.W + sB.W, -CMAX, CMAX)
before = acc(sM, every, allk)
dx, dy = dream(mM, range(10), NDREAM, 7); sM.practise(dx, dy, allk, epochs=2)
R["merge_0to4_plus_5to9"] = {"chip_A_alone": acc(sA, every, kA), "chip_B_alone": acc(sB, every, kB),
                             "added_tables_no_sleep": before, "after_one_night": acc(sM, every, allk)}
print("merge", R["merge_0to4_plus_5to9"], flush=True)
# few-shot
R["few_shot"] = {}
for k in (1, 5, 20):
    a, e, mm = [], [], []
    for s in range(3):
        r = np.random.RandomState(s)
        idx = np.concatenate([r.choice(np.where(ytr == c)[0], k, replace=False) for c in range(10)])
        a.append(acc(SurpriseTable(NB, 10, cmax=CMAX).practise(ctr[idx], ytr[idx], allk, epochs=10, seed=s), every, allk))
        ov = cte.astype(np.int32) @ ctr[idx].astype(np.int32).T - ctr[idx].sum(1)[None] // 2     # overlap, size-corrected
        e.append(float((ytr[idx][ov.argmax(1)] == yte).mean()))
        b1, b2 = list(base.values())[-1]
        mm.append(mlp_acc(mlp_fit(b1[idx], ytr[idx], ep=50, seed=s, steps_min=300), b2, yte))
    R["few_shot"][f"{k}_per_class"] = {"table": float(np.mean(a)), "episodic": float(np.mean(e)), "mlp": float(np.mean(mm))}
    print("few-shot", k, R["few_shot"][f"{k}_per_class"], flush=True)
mem_bits = new_mem().bits() if DREAM != "count" else 10 * NB * 16
R["memory_KB"] = {"fast_table_5bit": 10 * NB * 5 / 8192, "dream_memory": mem_bits / 8192,
                  "feature_detectors": len(CH) * F * 25 / 8192}
print("memory KB", R["memory_KB"], f"done {time.time()-t0:.0f}s", flush=True)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", f"cortex_v3_{DS}_{DREAM}_n{NIGHT}.json")
json.dump(R, open(out, "w"), indent=1)
