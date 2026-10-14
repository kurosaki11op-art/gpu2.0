"""SPARK Cortex month-1 proof suite (v2): close the accuracy gap without giving up "never forgets" or "merges".

Brain core v2
  senses   : brightness receptors (2 levels) + retina centre-surround cells (on / off), or the cochlea for sound
  sensory  : feature detectors learned without labels from stage-1 data only (feature_layer.Features)
  stable   : concept cells, P per class, learn by counting within their own class (feature_layer.ConceptMemory)
  fast     : surprise-gated correction table (sleep.SurpriseTable)
  sleep    : before practising a new stage, concept cells dream old classes; the table practises on new + dreams
  decision : concept cells pick their top 2 classes, the table chooses between them
Baselines: MLP (784-256-10 or mel-256-10) with backprop; in stages: plain fine-tuning and replay of 20 stored
examples per old class. All SIMULATED on CPU.
usage: python proof_suite_v2.py DATA_DIR mnist|fashion|speech"""
import json, os, sys, time
import numpy as np, torch
from cortex_core import load
from feature_layer import Features, ConceptMemory
from sleep import SurpriseTable

D, DS = sys.argv[1], sys.argv[2]
P, NDREAM = 32, 6000
CHANNELS = (50, 150, ("on", 8), ("off", 8))
if DS == "speech":   # sound needs finer loudness steps: 8 receptor levels (like hair cells with staggered thresholds)
    CHANNELS = (20, 50, 80, 110, 140, 170, 200, 230, ("on", 8), ("off", 8))
stages = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
torch.manual_seed(0); np.random.seed(0); t0 = time.time()
if DS == "speech":
    import cochlea
    KIND = os.environ.get("COCHLEA", "res")                                  # res = resonator bank (v2), cascade = v1
    fn = cochlea.sound_picture_res if KIND == "res" else cochlea.sound_picture
    xtr, ytr, xte, yte = cochlea.load_speech(os.path.join(D, "speech"), os.path.join(D, f"speech_pics_{KIND}.npz"), fn)
    DS_TAG = f"speech_{KIND}_L8"
    btr, _, bte, _ = cochlea.log_mel(os.path.join(D, "speech"), os.path.join(D, "speech_mel.npz"))
    base = {"pictures": (xtr / 255.0, xte / 255.0), "log-mel": (btr, bte)}
else:
    xtr, ytr, xte, yte = load(D, DS)
    base = {"pixels": (xtr / 255.0, xte / 255.0)}
    DS_TAG = DS
ytr, yte = ytr.astype(np.int64), yte.astype(np.int64)
cache = os.path.join(D, f"codes_v2_{DS_TAG}.npz")
if os.path.exists(cache):
    z = np.load(cache); ctr, cte = z["tr"], z["te"]
else:
    src = xtr[np.isin(ytr, stages[0])][:12000]
    fes = [Features(128, thr=c).fit(src) for c in CHANNELS]
    enc = lambda x: np.concatenate([np.concatenate([f.encode(x[i:i + 5000]) for f in fes], 1) for i in range(0, len(x), 5000)])
    ctr, cte = enc(xtr), enc(xte); np.savez_compressed(cache, tr=ctr, te=cte)
NB = ctr.shape[1]
print(DS, "codes", ctr.shape, f"{time.time()-t0:.0f}s", flush=True)


def decide(cm, st, code, known):
    sc = cm.scores(code); sc[:, ~known] = -1e30
    tb = st.scores(code, known)
    top2 = np.argsort(-sc, 1)[:, :2]
    pick = top2[np.arange(len(top2)), np.take_along_axis(tb, top2, 1).argmax(1)]
    return sc.argmax(1), tb.argmax(1), pick


def brain(idx_stages, seed=0, cm=None, st=None, known=None):
    cm = cm or ConceptMemory(NB, 10, P=P, seed=seed); st = st or SurpriseTable(NB, 10)
    known = np.zeros(10, bool) if known is None else known
    hist = []
    for i, sel in enumerate(idx_stages):
        cs = np.unique(ytr[sel]); cm.learn(ctr[sel], ytr[sel]); old = np.where(known)[0]; known[cs] = True
        X, Y = ctr[sel], ytr[sel]
        if len(old):                                                       # sleep: dream old classes
            dx, dy = cm.dreams(old, NDREAM, seed=seed * 10 + i); X = np.concatenate([X, dx]); Y = np.concatenate([Y, dy])
        st.practise(X, Y, known, seed=seed * 10 + i)
        seen = np.isin(yte, np.where(known)[0])
        a = [float((p == yte[seen]).mean()) for p in decide(cm, st, cte[seen], known)]
        hist.append({"stage": i + 1, "concept": a[0], "table": a[1], "brain": a[2]})
    return cm, st, known, hist


def mlp_fit(X, y, m=None, ep=5, seed=0):
    m = m or torch.nn.Sequential(torch.nn.Linear(X.shape[1], 256), torch.nn.ReLU(), torch.nn.Linear(256, 10))
    opt = torch.optim.Adam(m.parameters(), 1e-3); Xt = torch.tensor(X, dtype=torch.float32); Yt = torch.tensor(y)
    g = torch.Generator().manual_seed(seed)
    for _ in range(ep):
        for b in torch.randperm(len(Xt), generator=g).split(64):
            opt.zero_grad(); torch.nn.functional.cross_entropy(m(Xt[b]), Yt[b]).backward(); opt.step()
    return m


def mlp_acc(m, X, y):
    with torch.no_grad():
        return float((m(torch.tensor(X, dtype=torch.float32)).argmax(1).numpy() == y).mean())


R = {"dataset": DS, "label": "SIMULATED", "concept_cells_per_class": P, "dreams_per_old_class": NDREAM, "code_bits": NB}
# all at once ----------------------------------------------------------------------------------------
cm, st, _, h = brain([np.arange(len(ytr))])
R["all_at_once"] = {"brain": h[0]["brain"], "concept": h[0]["concept"], "table": h[0]["table"]}
for k, (btr_, bte_) in base.items():
    R["all_at_once"][f"mlp_{k}"] = mlp_acc(mlp_fit(btr_, ytr), bte_, yte)
print("all at once", R["all_at_once"], f"{time.time()-t0:.0f}s", flush=True)
# in stages ------------------------------------------------------------------------------------------
sidx = [np.where(np.isin(ytr, s))[0] for s in stages]
_, _, _, R["stages_brain"] = brain(sidx)
for k, (btr_, bte_) in base.items():
    m = r = None; buf = []; hist = []
    for i, sel in enumerate(sidx):
        m = mlp_fit(btr_[sel], ytr[sel], m, ep=2)
        rs = np.concatenate([sel] + buf); r = mlp_fit(btr_[rs], ytr[rs], r, ep=2)
        buf += [np.random.RandomState(i).choice(np.where(ytr == c)[0], 20, replace=False) for c in stages[i]]
        seen = np.isin(yte, sum(stages[:i + 1], ()))
        hist.append({"stage": i + 1, "mlp": mlp_acc(m, bte_[seen], yte[seen]), "mlp_replay20": mlp_acc(r, bte_[seen], yte[seen])})
    R[f"stages_mlp_{k}"] = hist
for i in range(5):
    print("stage", i + 1, {k: round(v, 4) for k, v in R["stages_brain"][i].items() if k != "stage"},
          {k: {kk: round(vv, 4) for kk, vv in R[k][i].items() if kk != "stage"} for k in R if k.startswith("stages_mlp")}, flush=True)
# merge: chip A learns classes 0-4, chip B classes 5-9; merge = pool concept cells, then one sleep to rebuild the table
iA, iB = np.where(ytr < 5)[0], np.where(ytr >= 5)[0]
cA, sA, kA, _ = brain([iA], seed=1); cB, sB, kB, _ = brain([iB], seed=2)
cmM = cA.merge(cB); stM = SurpriseTable(NB, 10); allk = np.ones(10, bool)
dx, dy = cmM.dreams(range(10), NDREAM, seed=7); stM.practise(dx, dy, allk)
a = [float((p == yte).mean()) for p in decide(cmM, stM, cte, allk)]
R["merge_0to4_plus_5to9"] = {"chip_A_alone": float((decide(cA, sA, cte, kA)[2] == yte).mean()),
                             "chip_B_alone": float((decide(cB, sB, cte, kB)[2] == yte).mean()),
                             "merged_concept_only": a[0], "merged_after_one_sleep": a[2]}
print("merge", R["merge_0to4_plus_5to9"], flush=True)
R["memory_KB"] = {"concept_counts_16bit": 10 * P * NB * 2 / 1024, "concept_decision_table_4bit": 10 * P * NB * 0.5 / 1024,
                  "correction_table_8bit": 10 * NB / 1024, "feature_detectors": len(CHANNELS) * 128 * 25 / 8 / 1024}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", f"cortex_v2_{DS_TAG}.json")
json.dump(R, open(out, "w"), indent=1)
print(f"done {time.time()-t0:.0f}s")
