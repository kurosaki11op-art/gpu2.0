"""Dreams that keep co-occurrence (research note docs/research_weak_spots.md). Staged learning on clothing (5 stages of 2
classes, margin 32, ndream 6000, night 2, night_stop 2, daydream 1 = today's rule) with the dream source swapped:
  base        : today (each bit drawn independently from the class on-rate; the chip's numba _dream)
  mix K       : K prototypes per class (competitive learning: an example updates the prototype with the highest mean rate over
                its active bits; the first K examples of a class seed the prototypes); a dream picks a prototype in proportion
                to its size and draws bits from that prototype's rates
  ex M p      : M stored real codes per class (reservoir sample); with probability p a dream is a stored code replayed exactly,
                otherwise the independent dream
  cue M p f   : like ex, but the stored code loses a fraction f of its on-bits and gets as many new bits drawn from the class
                rates (cue-and-complete)
Exact integer table rule (_practise, _count of cortex_int); the dream generators here use floating rates (exploration of
what is worth building; the chip would use counters and shifts). 3 seeds, python copy of cortex_int._stage.
usage: DATA_DIR DS [variant ...]   (DS = fashion | mnist | speech; speech uses the aligned codes)"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_core import load
from cortex_int import CortexInt, _count, _practise, _dream
D, DS = sys.argv[1], sys.argv[2]
if DS == "speech":
    z = np.load(os.path.join(D, "sep_speech_align_F64_p2.npz")); f_ = np.load(os.path.join(D, "speech_framesums_int.npz"))
    y_, te_ = f_["y"], f_["te"]; ytr, yte = y_[~te_], y_[te_]
else:
    z = np.load(os.path.join(D, f"sep_{DS}_F32_p2.npz")); _, ytr, _, yte = load(D, DS)
ctr, cte = z["tr"], z["te"]; ytr = ytr.astype(np.int64); yte = yte.astype(np.int64); NB = ctr.shape[1]


class Dreamer:
    def __init__(self, kind, K=4, M=10, p=0.5, f=0.15, q=0, B=0, seed=0):
        self.kind, self.K, self.M, self.p, self.f, self.q, self.B = kind, K, M, p, f, q, B
        self.r = np.random.RandomState(seed + 99)
        self.P = {}; self.Pn = {}; self.ex = {}; self.seen = {}

    def observe(self, c, a):
        if self.kind in ("mix",):
            if c not in self.P:
                self.P[c] = np.zeros((self.K, NB), np.float32); self.Pn[c] = np.zeros(self.K, np.int64)
            n = self.Pn[c]
            if (n == 0).any():
                j = int(np.argmax(n == 0))
            else:
                j = int(np.argmax(self.P[c][:, a].sum(1) / n))
            self.P[c][j, a] += 1; n[j] += 1
            if self.B and n[j] > (1 << self.B) - 1:                 # B-bit counters: halve the prototype when full (as the chip does per class)
                self.P[c][j] = np.floor(self.P[c][j] / 2); n[j] //= 2
        if self.kind in ("ex", "cue"):
            self.seen[c] = self.seen.get(c, 0) + 1; lst = self.ex.setdefault(c, [])
            if len(lst) < self.M:
                lst.append(a.copy())
            else:
                j = self.r.randint(self.seen[c])
                if j < self.M:
                    lst[j] = a.copy()

    def dream(self, c, on, n, rng, buf):
        if self.kind == "base":
            return _dream(on, n, c, rng, buf)
        if self.kind == "mix" and c in self.P and self.Pn[c].sum() > 0:
            pn = self.Pn[c]; j = self.r.choice(self.K, p=pn / pn.sum()) if (pn > 0).all() else int(np.argmax(pn))
            rate = self.P[c][j] / max(pn[j], 1)
            if self.q:                                              # rates kept with q bits
                rate = np.floor(rate * (1 << self.q)) / (1 << self.q)
            idx = np.nonzero(self.r.random_sample(NB) < rate)[0].astype(np.int32)
            buf[:len(idx)] = idx; return len(idx)
        if self.kind in ("ex", "cue") and c in self.ex and self.r.random_sample() < self.p:
            a = self.ex[c][self.r.randint(len(self.ex[c]))]
            if self.kind == "ex":
                buf[:len(a)] = a; return len(a)
            keep = a[self.r.random_sample(len(a)) >= self.f]; drop = len(a) - len(keep)
            rate = on[c].astype(np.float32) / max(int(n[c]), 1); extra = np.nonzero(self.r.random_sample(NB) < rate * (drop / max(rate.sum(), 1e-6)))[0]
            idx = np.unique(np.concatenate([keep, extra])).astype(np.int32); buf[:len(idx)] = idx; return len(idx)
        return _dream(on, n, c, rng, buf)


def stage(m, dr, idx, ndream=6000, night=2, night_stop=2, daydream=1):
    """python copy of cortex_int._stage (no context memory, no replay_k) with a pluggable dream source"""
    W, on, n, rng, known, margin, cmax, top = m.W, m.on, m.n, m.rng, m.known, m.margin, m.cmax, m.top
    y = ytr[idx]; new = np.unique(y); old = [c for c in np.where(known)[0] if c not in new]
    for c in new:
        known[c] = True
    buf = np.zeros(NB, np.int32); nreal = len(idx); total_d = ndream * len(old); done_d = rr = 0
    for i in range(nreal):
        a = np.nonzero(ctr[idx[i]])[0].astype(np.int32); c = int(y[i])
        _count(on, n, a, len(a), c, top); dr.observe(c, a)
        _practise(W, a, len(a), c, known, margin, cmax)
        for _ in range(daydream):
            k = dr.dream(c, on, n, rng, buf); _practise(W, buf, k, c, known, margin, cmax)
        due = (total_d * (i + 1)) // nreal
        while done_d < due:
            c2 = old[rr % len(old)]; rr += 1
            k = dr.dream(c2, on, n, rng, buf); _practise(W, buf, k, c2, known, margin, cmax); done_d += 1
    if old:
        kn = np.where(known)[0]; blockw = 0; cnt = 0; stop = False
        for p in range(night):
            for j in range(ndream * len(kn)):
                c2 = kn[j % len(kn)]; k = dr.dream(c2, on, n, rng, buf)
                blockw += _practise(W, buf, k, c2, known, margin, cmax); cnt += 1
                if night_stop > 0 and cnt % 256 == 0:
                    if blockw > night_stop:
                        stop = True; break
                    blockw = 0
            if stop:
                break


VARS = {"base": dict(kind="base"), "mix4_b8": dict(kind="mix", K=4, B=8), "mix4_b7": dict(kind="mix", K=4, B=7), "mix8_b7": dict(kind="mix", K=8, B=7), "mix8_b6": dict(kind="mix", K=8, B=6), "mix8_b5": dict(kind="mix", K=8, B=5), "mix8": dict(kind="mix", K=8), "mix3": dict(kind="mix", K=3), "mix4_q4": dict(kind="mix", K=4, q=4), "mix4_q3": dict(kind="mix", K=4, q=3), "mix4_q2": dict(kind="mix", K=4, q=2), "mix2": dict(kind="mix", K=2), "mix4": dict(kind="mix", K=4),
        "ex10_p.5": dict(kind="ex", M=10, p=0.5), "ex20_p.5": dict(kind="ex", M=20, p=0.5),
        "cue10_p.5_f.15": dict(kind="cue", M=10, p=0.5, f=0.15), "cue20_p.5_f.15": dict(kind="cue", M=20, p=0.5, f=0.15)}
names = sys.argv[3:] or list(VARS)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"dream_variants_{DS}.json")
res = json.load(open(out)) if os.path.exists(out) else {}
for name in names:
    accs = []
    for seed in (1, 2, 3):
        m = CortexInt(NB, seed=seed, night_stop=2, daydream=1); dr = Dreamer(seed=seed, **VARS[name])
        for i, s in enumerate([(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]):
            idx = np.where(np.isin(ytr, s))[0]; idx = idx[np.random.RandomState(100 * seed + i).permutation(len(idx))]
            stage(m, dr, idx)
        accs.append(round(float((m.predict(cte) == yte).mean()), 4))
    res[name] = {"acc": accs, "mean": round(float(np.mean(accs)), 4)}; print(name, res[name], flush=True)
    json.dump({"label": "SIMULATED (clothing, 5 stages, margin 32, 3 seeds, python stage copy with floating-rate dreams)", **res},
              open(out, "w"), indent=1)
