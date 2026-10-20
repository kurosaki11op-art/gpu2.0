"""Why do the newest words collapse under hard-example replay? (20 Oct 2026) DIAGNOSTIC, one seed, 20 words. Prints per stage: accuracy on each stage's words, night replays and writes; at the end where the last stage's test clips go. usage: SUBSET_DIR CACHE_DIR"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.argv_saved = sys.argv; import numpy as np
D, CACHE = sys.argv[1], sys.argv[2]; os.environ.update(HARD="1", CONS="1", REALMIX=os.environ.get("MIX", "8"))
import cortex_rules
from cortex_slow import CortexSlow
NW = 20; ROOT = D
ALL = sorted(d for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d))); WORDS = [ALL[i] for i in sorted(np.random.RandomState(0).permutation(len(ALL))[:NW])]
y, spk = [], []
for wi, w in enumerate(WORDS):
    for f in sorted(os.listdir(os.path.join(ROOT, w))): y.append(wi); spk.append(int(f.split("_")[0], 16))
y = np.array(y); te = (np.array(spk) % 5) == 0; ytr, yte = y[~te], y[te]; STAGES = [tuple(range(4 * i, 4 * i + 4)) for i in range(5)]
Ctr = np.concatenate([np.load(os.path.join(CACHE, "ch_peak_nw20_c%d.npz" % c))["tr"] for c in range(10)], 1); Cte = np.concatenate([np.load(os.path.join(CACHE, "ch_peak_nw20_c%d.npz" % c))["clean"] for c in range(10)], 1)
E = int(os.environ.get("E", 16)); seed = int(os.environ.get("SEED", 1))
for name, mk in (("shipped", lambda: CortexSlow(Ctr.shape[1], n_cls=NW, ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1)),
                 ("hard replay E=%d" % E, lambda: cortex_rules.CortexRules(Ctr.shape[1], rule="real", par=E, n_cls=NW, ch=100, K=5, night_stop=2, daydream=1, seed=seed, margin=256, ndream=1500, night=1))):
    m = mk(); print("==", name)
    for i, s in enumerate(STAGES):
        sel = np.where(np.isin(ytr, s))[0]; sel = sel[np.random.RandomState(100 * seed + i).permutation(len(sel))]; s0 = m.stats.copy(); m.stage(Ctr[sel], ytr[sel]); p = m.predict(Cte)
        accs = [round(float((p[np.isin(yte, st)] == yte[np.isin(yte, st)]).mean()), 2) for st in STAGES[:i + 1]]
        print("after stage", i, "per-stage accuracy so far", accs, "| night replays %d writes %d" % (m.stats[0] - s0[0], m.stats[1] - s0[1]), flush=True)
    last = np.isin(yte, STAGES[-1]); p = m.predict(Cte); print("last-stage test clips go to:", {WORDS[c]: int((p[last] == c).sum()) for c in np.unique(p[last])}, "(own words:", [WORDS[c] for c in STAGES[-1]], ")")
    print("share of all test decisions per class:", {WORDS[c]: round(float((p == c).mean()), 3) for c in range(NW)})
