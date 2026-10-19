"""Novelty recruitment on the margin signal (19 Oct 2026). SIMULATED. Blended stream (no stage boundary, sleep from surprise pressure, context = classes rewarded among the last R rewards) with very few labels.
Arm ctx : as brain_strict_digits.py `ctx` (pseudo-labels only among recently rewarded classes).
Arm ctxn: additionally, an unlabelled example whose top-2 margin is below the NOV percentile of recent rewarded margins is NOVEL; novel examples (at least 10 in a chunk) go to an anonymous class slot (ids 10..19, one open slot at a time, closed when it holds
  400 examples); unlabelled examples may also be pseudo-labelled to a slot. A rewarded example that the chip places in an unnamed slot names it (alias slot -> label). At test an unnamed slot counts as wrong.
usage: DATA_DIR; env SEEDS, NOV (percentile, default 10), R, ARMS=ctx:P,ctxn:P,..."""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_slow import CortexSlow, _stage_slow
import detector_learn
D = sys.argv[1]; DS = os.environ.get("DS", "mnist"); NPS = int(os.environ.get("NPS", 2000)); SEEDS = int(os.environ.get("SEEDS", 3)); NOV = float(os.environ.get("NOV", 10)); R = int(os.environ.get("R", 60))
ARMS = os.environ.get("ARMS", "ctx:0.02,ctxn:0.02,ctx:0.01,ctxn:0.01,ctx:0.005,ctxn:0.005").split(","); STAGES = [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]; t0 = time.time()
xtr, ytr, xte, yte = load(D, DS); ytr = ytr.astype(np.int64); yte = yte.astype(np.int64)
rs = np.random.RandomState(5); idx = np.concatenate([rs.permutation(np.where(np.isin(ytr, s))[0])[:NPS] for s in STAGES]); xtr, ytr = xtr[idx], ytr[idx]
ti = rs.permutation(len(xte))[:2000]; xte, yte = xte[ti], yte[ti]
fes = detector_learn.learn_features(xtr[np.isin(ytr, STAGES[0])])
enc = lambda x: np.concatenate([np.concatenate([g.encode(x[i:i + 2000]) for g in fes], 1) for i in range(0, len(x), 2000)])
ctr, cte = enc(xtr), enc(xte); NB = ctr.shape[1]


def night(m):
    old = np.where(m.known)[0].astype(np.int64)
    _, m.tick = _stage_slow(m.W, m.S, m.on, m.n, m.rng, m.known, np.zeros((0, 1), np.int32), np.zeros(0, np.int32), np.zeros(0, np.int64), np.zeros(0, np.int64), old,
                            m.ndream, 2, m.margin, m.cmax, m.top, m.daydream, m.night_stop, m.stats, m.ch, m.K, m.FR, m.RND, m.tick)


def scores(m, c, allowed):
    s = c.astype(np.int32) @ m.S.T; s[:, ~m.known] = -(1 << 30)
    if allowed is not None: s[:, ~np.isin(np.arange(s.shape[1]), allowed)] = -(1 << 30)
    return s


def best2(s):
    o = np.sort(s, 1); return s.argmax(1), o[:, -1] - o[:, -2]


def run(arm, seed):
    kind, p = arm.split(":"); frac = float(p); nov_on = kind == "ctxn"
    m = CortexSlow(NB, n_cls=20, ch=100, K=5, night_stop=2, daydream=1, seed=seed); m.night = 0
    order = [np.where(np.isin(ytr, s))[0] for s in STAGES]; order = [o[np.random.RandomState(100 * seed + i).permutation(len(o))] for i, o in enumerate(order)]
    rg = np.random.RandomState(31 * seed); allidx = np.concatenate(order); key = np.concatenate([np.full(len(o), i, float) for i, o in enumerate(order)]) + rg.uniform(-0.8, 0.8, len(allidx))
    stream = allidx[np.argsort(key)]; recent = []; buf = []; alias = np.full(20, -1); alias[:10] = np.arange(10); cur = -1; cur_n = 0; nxt = 10; since = 0; opened = 0
    for j in range(0, len(stream), 250):
        u = stream[j:j + 250]; lm = rg.rand(len(u)) < frac; lab, unl = u[lm], u[~lm]
        anon = [a for a in range(10, nxt)]
        if len(lab):
            allk = np.where(m.known)[0]
            if nov_on and len(allk):                                           # a rewarded example placed in an unnamed slot names it
                pr, _ = best2(scores(m, ctr[lab], allk))
                for pi, yi in zip(pr, ytr[lab]):
                    if pi >= 10 and alias[pi] < 0: alias[pi] = yi
            since += int(m.stage(ctr[lab], ytr[lab])); recent += list(ytr[lab])
        allowed = np.unique(recent[-R:]) if len(recent) else np.zeros(0, np.int64)
        if nov_on: allowed = np.union1d(allowed, np.array(anon, np.int64))
        if len(allowed) and len(lab):
            _, mg0 = best2(scores(m, ctr[lab], allowed)); buf = (buf + list(mg0))[-200:]
        if len(buf) >= 10 and len(unl) and len(allowed):
            tau = np.percentile(buf, 0); pred, mg = best2(scores(m, ctr[unl], allowed)); sel = mg >= tau
            if nov_on:
                tn = np.percentile(buf, NOV); novel = mg < tn; sel &= ~novel
                if novel.sum() >= 10 and nxt < 20 or (novel.sum() >= 10 and cur >= 0):
                    if cur < 0 or cur_n >= 400: cur = nxt; nxt += 1; cur_n = 0; opened += 1
                    since += int(m.stage(ctr[unl][novel], np.full(int(novel.sum()), cur, np.int64))); cur_n += int(novel.sum())
            if sel.any(): since += int(m.stage(ctr[unl][sel], pred[sel]))
        if since >= 500: night(m); since = 0
    night(m)
    allk = np.where(m.known)[0]; pr, _ = best2(scores(m, cte, allk)); mapped = alias[pr]
    return float((mapped == yte).mean()), {"slots_opened": opened, "slots_named": int((alias[10:] >= 0).sum())}


res = {}
for arm in ARMS:
    a = []; inf = []
    for seed in range(1, SEEDS + 1):
        r, i = run(arm, seed); a.append(r); inf.append(i); print(arm, "seed", seed, round(r, 4), i, "%.0fs" % (time.time() - t0), flush=True)
    res[arm] = {"acc": round(float(np.mean(a)), 4), "seeds": [round(x, 4) for x in a], "info": inf}; json.dump(res, open("brain_strict_novel_%s.json" % DS, "w"), indent=1)
print(json.dumps({k: v["acc"] for k, v in res.items()}))
