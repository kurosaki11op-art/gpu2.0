"""Brain-strict learning tests on digits (21 Oct 2026). SIMULATED, exact integer chip model (CortexSlow, K = 5, ch = 100), 5 stages of 2 digits.
Audit: docs/brain_principles_audit.md. Arms (env ARMS, comma list):
  base      shipped path: every example labelled, host calls each stage and its night (reference)
  chunk     same labels, but the stage is fed in chunks and the night is one separate call (checks the structure change alone)
  few:P     only fraction P of each stage's examples are labelled (the reward); labelled ones come first and name the classes
            (no class list from the host); the unlabelled ones get the chip's own winner as label only when the winner is clear
            (top-2 margin >= the lower quartile of the labelled examples' margins), otherwise they are ignored; one night at the end of the stage
  fewc:P:Q  like few, but a pseudo-label may only be one of the classes rewarded in the current context (the stage's labelled ones), margin cut at percentile Q (default 25)
  press:T   no stage boundaries for sleep: the stream is fed in chunks, the chip sleeps (one night) when the surprise writes since its last sleep reach T
Detectors: env DET=fit (Features.fit, batch, offline) or DET=chip (one-pass on-chip rule, detector_learn.learn_features).
usage: python brain_strict_digits.py DATA_DIR  (DATA_DIR holds mnist.npz); env NPS (examples per stage, default 2000), SEEDS (default 3)"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow, _stage_slow
from feature_layer import Features
import detector_learn

D = sys.argv[1]; NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 3)); DET = os.environ.get("DET", "fit")
ARMS = os.environ.get("ARMS", "base,chunk,few:0.1,few:0.25,press:3000").split(","); OUT = os.environ.get("OUT", "brain_strict_%s_%s.json" % (os.environ.get("DS", "mnist"), DET))
CH = (50, 150, ("on", 8), ("off", 8)); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
DS = os.environ.get("DS", "mnist"); xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
first = xtr[np.isin(ytr, STAGES[0])]
fes = detector_learn.learn_features(first) if DET == "chip" else [Features(32, thr=c).fit(first[:12000]) for c in CH]
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
ctr, cte = enc(xtr), enc(xte); print("codes", ctr.shape, "%.0fs" % (time.time() - t0), flush=True)
NB = ctr.shape[1]; EMPTY = (np.zeros((0, NB), np.uint8), np.zeros(0, np.int64))


def chip(seed): return CortexSlow(NB, ch=100, K=5, night_stop=2, daydream=1, seed=seed)


def night(m):
    """night only: no examples, dreams of every known class (the same njit loop as a stage with zero real examples)"""
    old = np.where(m.known)[0].astype(np.int64)
    _, m.tick = _stage_slow(m.W, m.S, m.on, m.n, m.rng, m.known, np.zeros((0, 1), np.int32), np.zeros(0, np.int32), np.zeros(0, np.int64), np.zeros(0, np.int64), old,
                            m.ndream, 2, m.margin, m.cmax, m.top, m.daydream, m.night_stop, m.stats, m.ch, m.K, m.FR, m.RND, m.tick)


def acc(m): return float((m.predict(cte) == yte).mean())


def margins(m, c, allowed=None):
    s = c.astype(np.int32) @ m.S.T; s[:, ~m.known] = -(1 << 30)
    if allowed is not None: s[:, ~np.isin(np.arange(s.shape[1]), allowed)] = -(1 << 30)
    o = np.sort(s, 1); return s.argmax(1), o[:, -1] - o[:, -2]


def run(arm, seed):
    m = chip(seed); info = {}
    kind, _, p = arm.partition(":")
    order = [np.where(np.isin(ytr, s))[0] for s in STAGES]
    order = [o[np.random.RandomState(100 * seed + i).permutation(len(o))] for i, o in enumerate(order)]
    if kind == "base":
        for o in order: m.stage(ctr[o], ytr[o])
    elif kind == "chunk":
        m.night = 0
        for o in order:
            for j in range(0, len(o), 250): m.stage(ctr[o[j:j + 250]], ytr[o[j:j + 250]])
            night(m)
    elif kind in ("few", "fewc"):
        ps = p.split(":"); frac = float(ps[0]); q = float(ps[1]) if len(ps) > 1 else 25; m.night = 0; ok = tot = used = 0
        for o in order:
            k = max(2, int(len(o) * frac)); lab, unl = o[:k], o[k:]
            m.stage(ctr[lab], ytr[lab])
            al = np.unique(ytr[lab]) if kind == "fewc" else None          # fewc: only classes rewarded in this context may be chosen
            _, mg = margins(m, ctr[lab], al); tau = np.percentile(mg, q)
            for j in range(0, len(unl), 250):
                u = unl[j:j + 250]; pred, mg = margins(m, ctr[u], al); sel = mg >= tau
                tot += int(sel.sum()); ok += int((pred[sel] == ytr[u][sel]).sum())
                if sel.any(): m.stage(ctr[u][sel], pred[sel])
            night(m); used += k
        info = {"labelled": used, "pseudo_used": tot, "pseudo_precision": round(ok / max(tot, 1), 4)}
    elif kind == "press":
        thr = int(p); m.night = 0; since = 0; sleeps = 0
        for o in order:
            for j in range(0, len(o), 250):
                since += int(m.stage(ctr[o[j:j + 250]], ytr[o[j:j + 250]]))
                if since >= thr: night(m); since = 0; sleeps += 1
        night(m); sleeps += 1; info = {"sleeps": sleeps}
    return acc(m), info


res = {}
for arm in ARMS:
    a = []; inf = []
    for seed in range(1, SEEDS + 1):
        r, i = run(arm, seed); a.append(r); inf.append(i); print(arm, "seed", seed, round(r, 4), i, "%.0fs" % (time.time() - t0), flush=True)
    res[arm] = {"acc": round(float(np.mean(a)), 4), "seeds": [round(x, 4) for x in a], "info": inf}; json.dump(res, open(OUT, "w"), indent=1)
print(json.dumps({k: v["acc"] for k, v in res.items()}))
