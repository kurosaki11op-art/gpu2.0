"""Brain-strict learning tests on digits (21 Oct 2026). SIMULATED, exact integer chip model (CortexSlow, K = 5, ch = 100), 5 stages of 2 digits.
Audit: docs/brain_principles_audit.md. Arms (env ARMS, comma list):
  base      shipped path: every example labelled, host calls each stage and its night (reference)
  chunk     same labels, but the stage is fed in chunks and the night is one separate call (checks the structure change alone)
  few:P     only fraction P of each stage's examples are labelled (the reward); labelled ones come first and name the classes
            (no class list from the host); the unlabelled ones get the chip's own winner as label only when the winner is clear
            (top-2 margin >= the lower quartile of the labelled examples' margins), otherwise they are ignored; one night at the end of the stage
  fewa:P:Q  like fewc, and the fast table must name the same class as the slow table before a pseudo-label is used
  gate:v|1  every label is present; an example is learned (with its true label) only if its 5 shifted views agree on one class; v = learn all 5 views, 1 = centre view only
  act:P     active labelling: a random seed of at most 40 labels, then labels requested for the lowest-margin examples up to the budget P of the stage, then agreement-gated pseudo-labels (as fewa)
  lab:P     control: only the labelled fraction P of each stage is learned (no pseudo-labels), to show how much the pseudo-labels add
  fews:P:Q  like fewc, with eye movements: labelled and pseudo-labelled examples are learned with their 4 one-pixel-shifted views, and an unlabelled example is pseudo-labelled only if all 5 views name the same class
  fewc:P:Q  like few, but a pseudo-label may only be one of the classes rewarded in the current context (the stage's labelled ones), margin cut at percentile Q (default 25)
  mixc:P:Q  like fewc, but the rewards arrive scattered through the stream; the margin cut comes from the margins of the most recent 200 rewarded examples (percentile Q)
  ctx:P:Q:R   no stage boundaries: the stages blend in one stream, sleep comes from pressure, and the context is the set of classes rewarded among the last R rewards (P = labelled fraction, Q = margin percentile; P = 1 is the all-labelled control)
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


SH = None


def shifted_codes():
    """codes of the training images under the views of env VIEWS (built once, only for arms that use them): s1 = one-pixel shifts right / left / down / up (default), s2 = two-pixel shifts, d = one-pixel diagonal shifts,
    sc = two small scale changes (0.93 and 1.07 about the centre), and combinations s12 (s1 + s2), s1sc (s1 + sc), s1d (s1 + d). The centre view is always used too."""
    global SH
    if SH is None:
        X = xtr.reshape(len(xtr), 28, 28); SH = []

        def shift(dy, dx):
            out = np.zeros_like(X); ys, yd = (slice(0, 28 - dy), slice(dy, 28)) if dy >= 0 else (slice(-dy, 28), slice(0, 28 + dy)); xs, xd = (slice(0, 28 - dx), slice(dx, 28)) if dx >= 0 else (slice(-dx, 28), slice(0, 28 + dx))
            out[:, yd, xd] = X[:, ys, xs]; return out

        def scale(k):
            src = np.round(13.5 + (np.arange(28) - 13.5) / k).astype(int); ok = (src >= 0) & (src <= 27); src = np.clip(src, 0, 27)
            out = X[:, src][:, :, src]; out[:, ~ok, :] = 0; out[:, :, ~ok] = 0; return out

        SPEC = {"s1": [(0, 1), (0, -1), (1, 0), (-1, 0)], "s2": [(0, 2), (0, -2), (2, 0), (-2, 0)], "d": [(1, 1), (-1, -1), (1, -1), (-1, 1)]}
        ALIAS = {"s1": ["s1"], "s2": ["s2"], "d": ["d"], "sc": ["sc"], "s12": ["s1", "s2"], "s1sc": ["s1", "sc"], "s1d": ["s1", "d"]}; imgs = []
        for tag in ALIAS[os.environ.get("VIEWS", "s1")]:
            imgs += [scale(k) for k in (0.93, 1.07)] if tag == "sc" else [shift(*v) for v in SPEC[tag]]
        for im in imgs: SH.append(enc(im.reshape(len(X), -1)))
        print("views", os.environ.get("VIEWS", "s1"), "->", len(SH) + 1, "views per example", flush=True)
    return SH


CFG = dict(margin=int(os.environ.get('MARGIN', 32)), ndream=int(os.environ.get('NDREAM', 6000)), night=int(os.environ.get('NIGHT', 2)))   # chip settings; shipped 32 / 6,000 / 2, recommended 19 Oct: 256 / 1,500 / 1


def chip(seed): return CortexSlow(NB, ch=100, K=5, night_stop=2, daydream=1, seed=seed, **CFG)


def night(m):
    """night only: no examples, dreams of every known class (the same njit loop as a stage with zero real examples)"""
    old = np.where(m.known)[0].astype(np.int64)
    _, m.tick = _stage_slow(m.W, m.S, m.on, m.n, m.rng, m.known, np.zeros((0, 1), np.int32), np.zeros(0, np.int32), np.zeros(0, np.int64), np.zeros(0, np.int64), old,
                            m.ndream, CFG['night'], m.margin, m.cmax, m.top, m.daydream, m.night_stop, m.stats, m.ch, m.K, m.FR, m.RND, m.tick)


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
    elif kind in ("few", "fewc", "fewa"):
        ps = p.split(":"); frac = float(ps[0]); q = float(ps[1]) if len(ps) > 1 else 25; m.night = 0; ok = tot = used = 0
        for o in order:
            k = max(2, int(len(o) * frac)); lab, unl = o[:k], o[k:]
            m.stage(ctr[lab], ytr[lab])
            al = np.unique(ytr[lab]) if kind in ("fewc", "fewa") else None          # fewc: only classes rewarded in this context may be chosen
            _, mg = margins(m, ctr[lab], al); tau = np.percentile(mg, q)
            for j in range(0, len(unl), 250):
                u = unl[j:j + 250]; pred, mg = margins(m, ctr[u], al); sel = mg >= tau
                if kind == "fewa":                                            # fast and slow table must name the same class (hippocampus and cortex agree)
                    sw = ctr[u].astype(np.int32) @ m.W.T.astype(np.int32); sw[:, ~np.isin(np.arange(sw.shape[1]), al)] = -(1 << 30); sw[:, ~m.known] = -(1 << 30); sel &= sw.argmax(1) == pred
                tot += int(sel.sum()); ok += int((pred[sel] == ytr[u][sel]).sum())
                if sel.any(): m.stage(ctr[u][sel], pred[sel])
            night(m); used += k
        info = {"labelled": used, "pseudo_used": tot, "pseudo_precision": round(ok / max(tot, 1), 4)}
    elif kind == "fewk":                                                     # Module 2: sleep category formation. Unlabelled codes wait in a bounded buffer of B; the codes of one buffer that overlap most (popcount of AND) pull each other's class scores together (K neighbours), the pooled winner must clear the margin cut and agree with the fast table
        ps = p.split(":"); frac = float(ps[0]); q = float(ps[1]); KN = int(ps[2]); B = int(ps[3]); m.night = 0; ok = tot = used = 0
        for o in order:
            k = max(2, int(len(o) * frac)); lab, unl = o[:k], o[k:]
            m.stage(ctr[lab], ytr[lab]); al = np.unique(ytr[lab]); mask = ~np.isin(np.arange(10), al)
            sc = lambda c: np.where((mask | ~m.known)[None, :], -(1 << 30), c.astype(np.int32) @ m.S.T)
            s0 = sc(ctr[lab]); o2 = np.sort(s0, 1); tau = np.percentile(o2[:, -1] - o2[:, -2], q)
            for j in range(0, len(unl), B):
                u = unl[j:j + B]; c = ctr[u]; s = sc(c).astype(np.int64); ov = c.astype(np.int32) @ c.T.astype(np.int32); np.fill_diagonal(ov, -1)
                nn = np.argsort(-ov, 1)[:, :KN]; ok_cls = ~(mask | ~m.known)[None, :]
                z = np.where(ok_cls, s, 0); pooled = z + z[nn].sum(1)                  # own scores plus the neighbours' scores
                pooled = np.where(ok_cls, pooled, -(1 << 40)); pred = pooled.argmax(1); op = np.sort(pooled, 1); mg = (op[:, -1] - op[:, -2]) // (KN + 1)
                sw = c.astype(np.int32) @ m.W.T.astype(np.int32); sw[:, mask | ~m.known] = -(1 << 30); sel = (mg >= tau) & (sw.argmax(1) == pred)
                tot += int(sel.sum()); ok += int((pred[sel] == ytr[u][sel]).sum())
                if sel.any(): m.stage(c[sel], pred[sel])
            night(m); used += k
        info = {"labelled": used, "pseudo_used": tot, "pseudo_precision": round(ok / max(tot, 1), 4)}
    elif kind == "fewkv":                                                     # Module 2 + eye movements: sleep category formation. Unlabelled codes wait in a bounded buffer of B; the codes of one buffer that overlap most (popcount of AND) pull each other's class scores together (K neighbours), the pooled winner must clear the margin cut and agree with the fast table
        ps = p.split(":"); frac = float(ps[0]); q = float(ps[1]); KN = int(ps[2]); B = int(ps[3]); m.night = 0; ok = tot = used = 0; sh = shifted_codes(); views = lambda idx: np.concatenate([ctr[idx]] + [v[idx] for v in sh])
        for o in order:
            k = max(2, int(len(o) * frac)); lab, unl = o[:k], o[k:]
            m.stage(views(lab), np.tile(ytr[lab], len(sh) + 1)); al = np.unique(ytr[lab]); mask = ~np.isin(np.arange(10), al)
            sc = lambda c: np.where((mask | ~m.known)[None, :], -(1 << 30), c.astype(np.int32) @ m.S.T)
            s0 = sc(ctr[lab]); o2 = np.sort(s0, 1); tau = np.percentile(o2[:, -1] - o2[:, -2], q)
            for j in range(0, len(unl), B):
                u = unl[j:j + B]; c = ctr[u]; s = sc(c).astype(np.int64); ov = c.astype(np.int32) @ c.T.astype(np.int32); np.fill_diagonal(ov, -1)
                nn = np.argsort(-ov, 1)[:, :KN]; ok_cls = ~(mask | ~m.known)[None, :]
                z = np.where(ok_cls, s, 0); pooled = z + z[nn].sum(1)                  # own scores plus the neighbours' scores
                pooled = np.where(ok_cls, pooled, -(1 << 40)); pred = pooled.argmax(1); op = np.sort(pooled, 1); mg = (op[:, -1] - op[:, -2]) // (KN + 1)
                sw = c.astype(np.int32) @ m.W.T.astype(np.int32); sw[:, mask | ~m.known] = -(1 << 30); sel = (mg >= tau) & (sw.argmax(1) == pred)
                for v in sh: sel &= margins(m, v[u], al)[0] == pred                      # every shifted view must name the same class
                tot += int(sel.sum()); ok += int((pred[sel] == ytr[u][sel]).sum())
                if sel.any(): m.stage(views(u[sel]), np.tile(pred[sel], len(sh) + 1))
            night(m); used += k
        info = {"labelled": used, "pseudo_used": tot, "pseudo_precision": round(ok / max(tot, 1), 4)}
    elif kind == "fews":
        ps = p.split(":"); frac = float(ps[0]); q = float(ps[1]); m.night = 0; ok = tot = used = 0; sh = shifted_codes()
        views = lambda idx: np.concatenate([ctr[idx]] + [v[idx] for v in sh])
        for o in order:
            k = max(2, int(len(o) * frac)); lab, unl = o[:k], o[k:]
            m.stage(views(lab), np.tile(ytr[lab], len(sh) + 1)); al = np.unique(ytr[lab]); _, mg = margins(m, ctr[lab], al); tau = np.percentile(mg, q)
            for j in range(0, len(unl), 250):
                u = unl[j:j + 250]; pred, mg = margins(m, ctr[u], al); sel = mg >= tau
                for v in sh: sel &= margins(m, v[u], al)[0] == pred            # every shifted view must name the same class
                tot += int(sel.sum()); ok += int((pred[sel] == ytr[u][sel]).sum())
                if sel.any(): m.stage(views(u[sel]), np.tile(pred[sel], len(sh) + 1))
            night(m); used += k
        info = {"labelled": used, "pseudo_used": tot, "pseudo_precision": round(ok / max(tot, 1), 4)}
    elif kind == "act":                                                      # active labelling: a small random seed, then the chip asks for labels on the examples it is least sure about (lowest top-2 margin), then pseudo-labels the rest like fewa
        frac = float(p); m.night = 0; ok = tot = used = 0
        for o in order:
            budget = max(4, int(len(o) * frac)); k0 = min(budget // 2, 40); seed_ix = o[:k0]; rest = o[k0:]
            m.stage(ctr[seed_ix], ytr[seed_ix]); al = np.unique(ytr[seed_ix]); _, mg = margins(m, ctr[rest], al)
            q = rest[np.argsort(mg)[:budget - k0]]; m.stage(ctr[q], ytr[q]); al = np.unique(np.concatenate([ytr[seed_ix], ytr[q]]))
            unl = np.setdiff1d(rest, q); _, mg = margins(m, ctr[q], al); tau = np.percentile(mg, 0)
            for j in range(0, len(unl), 250):
                u = unl[j:j + 250]; pred, mg = margins(m, ctr[u], al); sel = mg >= tau
                sw = ctr[u].astype(np.int32) @ m.W.T.astype(np.int32); sw[:, ~np.isin(np.arange(sw.shape[1]), al)] = -(1 << 30); sw[:, ~m.known] = -(1 << 30); sel &= sw.argmax(1) == pred
                tot += int(sel.sum()); ok += int((pred[sel] == ytr[u][sel]).sum())
                if sel.any(): m.stage(ctr[u][sel], pred[sel])
            night(m); used += budget
        info = {"labelled": used, "pseudo_used": tot, "pseudo_precision": round(ok / max(tot, 1), 4)}
    elif kind == "lab":                                                      # control: only the labelled examples are used (no pseudo-labels at all), same stage and night structure
        frac = float(p); m.night = 0
        for o in order:
            k = max(2, int(len(o) * frac)); lab = o[:k]; m.stage(ctr[lab], ytr[lab]); night(m)
        info = {"labelled": int(sum(max(2, int(len(o) * frac)) for o in order))}
    elif kind == "gate":
        use_views = p == "v"; m.night = 0; kept = tot = 0; sh = shifted_codes()
        views = lambda idx: np.concatenate([ctr[idx]] + [v[idx] for v in sh]) if use_views else ctr[idx]
        for o in order:                                                      # every label is present; an example is learned only if its 5 views agree on one class (the eyes are not fooled by it)
            for j in range(0, len(o), 500):
                u = o[j:j + 500]; pc, _ = margins(m, ctr[u]); ok = np.ones(len(u), bool)
                for v in sh: ok &= margins(m, v[u])[0] == pc
                tot += len(u); kept += int(ok.sum())
                if ok.sum():
                    idx = u[ok]; m.stage(views(idx), np.tile(ytr[idx], len(sh) + 1 if use_views else 1))
            night(m)
        info = {"kept_fraction": round(kept / max(tot, 1), 4)}
    elif kind == "mixc":
        ps = p.split(":"); frac = float(ps[0]); q = float(ps[1]) if len(ps) > 1 else 50; m.night = 0; ok = tot = used = 0
        for o in order:
            rg = np.random.RandomState(7 * seed + len(o)); lab_mask = rg.rand(len(o)) < frac; lab_mask[:2] = True   # reward arrives scattered through the stream
            allowed = np.zeros(0, np.int64); buf = []
            for j in range(0, len(o), 250):
                u = o[j:j + 250]; lm = lab_mask[j:j + 250]; lab, unl = u[lm], u[~lm]
                if len(allowed):
                    _, mg0 = margins(m, ctr[lab], allowed); buf = (buf + list(mg0))[-200:]
                m.stage(ctr[lab], ytr[lab]); used += len(lab); allowed = np.union1d(allowed, np.unique(ytr[lab]))
                if len(buf) >= 10 and len(unl):
                    tau = np.percentile(buf, q); pred, mg = margins(m, ctr[unl], allowed); sel = mg >= tau
                    tot += int(sel.sum()); ok += int((pred[sel] == ytr[unl][sel]).sum())
                    if sel.any(): m.stage(ctr[unl][sel], pred[sel])
            night(m)
        info = {"labelled": used, "pseudo_used": tot, "pseudo_precision": round(ok / max(tot, 1), 4)}
    elif kind == "ctx":
        ps = p.split(":"); frac = float(ps[0]); q = float(ps[1]); R = int(ps[2]); thr = 500; m.night = 0; ok = tot = used = 0; since = 0; sleeps = 0
        rg = np.random.RandomState(31 * seed); allidx = np.concatenate(order); key = np.concatenate([np.full(len(o), i, float) for i, o in enumerate(order)]) + rg.uniform(-0.8, 0.8, len(allidx))
        stream = allidx[np.argsort(key)]; recent = []; buf = []                 # stages blend: no boundary is given; context = classes rewarded among the last R rewards
        for j in range(0, len(stream), 250):
            u = stream[j:j + 250]; lm = rg.rand(len(u)) < frac; lab, unl = u[lm], u[~lm]
            allowed = np.unique(recent[-R:]) if len(recent) else np.zeros(0, np.int64)
            if len(allowed) and len(lab):
                _, mg0 = margins(m, ctr[lab], allowed); buf = (buf + list(mg0))[-200:]
            if len(lab): since += int(m.stage(ctr[lab], ytr[lab])); used += len(lab); recent += list(ytr[lab])
            allowed = np.unique(recent[-R:]) if len(recent) else np.zeros(0, np.int64)
            if len(buf) >= 10 and len(unl) and len(allowed):
                tau = np.percentile(buf, q); pred, mg = margins(m, ctr[unl], allowed); sel = mg >= tau
                tot += int(sel.sum()); ok += int((pred[sel] == ytr[unl][sel]).sum())
                if sel.any(): since += int(m.stage(ctr[unl][sel], pred[sel]))
            if since >= thr: night(m); since = 0; sleeps += 1
        night(m); sleeps += 1; info = {"labelled": used, "pseudo_used": tot, "pseudo_precision": round(ok / max(tot, 1), 4), "sleeps": sleeps}
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
