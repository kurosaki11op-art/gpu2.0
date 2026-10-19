"""Unsupervised category layer + sparse naming (19 Oct 2026). SIMULATED. Brain principles: competitive Hebbian categories (no labels needed), recruitment of a new assembly on novelty or on a rewarded mismatch,
a label is a sparse reward that names the winning assembly (concept cells), one pass, no stored data. Integer only: add, compare, clip.
Each category k holds one signed 6-bit counter per code bit. Score = sum of its counters over the example's active bits (add only). The winner steps +1 on active bits, -1 on inactive bits (clip +-31).
  novelty: if the best score / active bits < R, a free category is recruited and seeded from the example.
  naming : a rewarded example adds 1 to the winner's label counter for its class (cap 255); if the winner already carries a different majority label, a new category is recruited and seeded from the example (error-driven recruitment).
Prediction: the winning category's majority label (categories with no label are skipped). 5 stages of 2 digits, labelled fraction P of examples (the first 2 of each stage always). usage: DATA_DIR; env DS, NPS, SEEDS, KMAX, ARMS=P:R:H,... (H = homeostasis shift, 0 = off)"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from numba import njit
from cortex_core import load
import detector_learn
D = sys.argv[1]; DS = os.environ.get("DS", "mnist"); NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 3)); KMAX = int(os.environ.get("KMAX", 100))
ARMS = [a.split(":") for a in os.environ.get("ARMS", "0.1:-2:4,0.1:-2:2").split(",")]; STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
ctr, cte = enc(xtr).astype(np.uint8), enc(xte).astype(np.uint8); NB = ctr.shape[1]


@njit(cache=True)
def run(codes, y, lab, cnt, labc, nk, R, wins, H):
    """stream the examples in order; lab[i] = 1 if the example is rewarded. cnt (K, NB) int8, labc (K, 10) int32, nk[0] = categories in use."""
    NBk = codes.shape[1]
    for i in range(len(codes)):
        na = 0
        for b in range(NBk): na += codes[i, b]
        if na == 0: continue
        best = -1; bs = -(1 << 30)
        for k in range(nk[0]):
            s = 0
            for b in range(NBk):
                if codes[i, b]: s += cnt[k, b]
            s -= (wins[k] >> H) if H > 0 else 0                    # homeostasis: a category that wins often is handicapped (shift only)
            if s > bs: bs = s; best = k
        recruit = best < 0 or bs < R * na                      # novelty: weak best match (score per active bit < R)
        if lab[i] and best >= 0 and not recruit:
            mx = 0; mj = -1
            for c in range(10):
                if labc[best, c] > mx: mx = labc[best, c]; mj = c
            if mj >= 0 and mj != y[i]: recruit = True              # rewarded mismatch spawns a new assembly
        if recruit and nk[0] < cnt.shape[0]:
            best = nk[0]; nk[0] += 1; wins[best] = 1
            for b in range(NBk): cnt[best, b] = 8 if codes[i, b] else -1
        elif best >= 0:
            wins[best] += 1
            for b in range(NBk):
                v = cnt[best, b] + (1 if codes[i, b] else -1)
                cnt[best, b] = 31 if v > 31 else (-31 if v < -31 else v)
        if lab[i] and best >= 0 and labc[best, y[i]] < 255: labc[best, y[i]] += 1


def predict(codes, cnt, labc, nk):
    out = np.zeros(len(codes), np.int64); named = np.where(labc[:nk[0]].sum(1) > 0)[0]
    s = codes.astype(np.int32) @ cnt[named].T.astype(np.int32); return labc[named][s.argmax(1)].argmax(1)


res = {}
for P, R, H in ARMS:
    P = float(P); R = int(R); H = int(H); acc = []; used = []
    for seed in range(1, SEEDS + 1):
        cnt = np.zeros((KMAX, NB), np.int8); labc = np.zeros((KMAX, 10), np.int32); nk = np.zeros(1, np.int64); wins = np.zeros(KMAX, np.int64)
        for i, s in enumerate(STAGES):
            o = np.where(np.isin(ytr, s))[0]; o = o[np.random.RandomState(100 * seed + i).permutation(len(o))]
            lab = (np.random.RandomState(7 * seed + i).rand(len(o)) < P).astype(np.uint8); lab[:2] = 1
            run(ctr[o], ytr[o], lab, cnt, labc, nk, R, wins, H)
        acc.append(float((predict(cte, cnt, labc, nk) == yte).mean())); used.append(int(nk[0]))
        print(DS, "labels", P, "R", R, "H", H, "seed", seed, "acc", round(acc[-1], 4), "categories", used[-1], flush=True)
    res["%s:%d:%d" % (P, R, H)] = {"acc": round(float(np.mean(acc)), 4), "seeds": [round(a, 4) for a in acc], "categories": used}
    json.dump(res, open("brain_strict_clusters_%s.json" % DS, "w"), indent=1)
print(json.dumps({k: v["acc"] for k, v in res.items()}))
