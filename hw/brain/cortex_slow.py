"""Slow consolidating table (Redesign 6, 18 Oct 2026). The fast table W is trained online (perceptron-like, 5-bit, margin rule), so its
final weights carry order noise from the last examples. A second table S (8-bit entries, 4 fractional bits) follows W in integer steps:
every CH practise ticks (a tick = one real example, or one night dream) S += (16*W - S) >> K. Prediction reads S. Shifts and adds only.
After a stage with fewer than 2*CH real examples (a few-shot stage) there is no time to consolidate: S is set to 16*W (small="copy") or only
the new classes' rows are copied (small="rows"), so an imprinted class is seen at once, and the short sleep that follows an imprint works on W as before, S then copies W again.
CortexSlow subclasses CortexInt; only the stage loop and predict differ."""
import numpy as np
from numba import njit
from cortex_int import CortexInt, _xs, _count, _practise, _dream


@njit(cache=True)
def _follow(S, W, K):
    for c in range(W.shape[0]):
        for b in range(W.shape[1]):
            S[c, b] += ((np.int32(16) * np.int32(W[c, b])) - S[c, b]) >> K


@njit(cache=True)
def _stage_slow(W, S, on, n, rng, known, acts, nacts, ys, new_cls, old_cls, ndream, night, margin, cmax, top, daydream, night_stop,
                stats, ch, K, tick0):
    buf = np.zeros(on.shape[1], np.int32)
    for c in new_cls:
        known[c] = True
    nreal = len(ys); total_d = ndream * len(old_cls); done_d = 0; rr = 0; writes = 0; tick = tick0
    for i in range(nreal):
        _count(on, n, acts[i], nacts[i], ys[i], top)
        writes += _practise(W, acts[i], nacts[i], ys[i], known, margin, cmax)
        for d in range(daydream):
            k = _dream(on, n, ys[i], rng, buf)
            writes += _practise(W, buf, k, ys[i], known, margin, cmax)
        due = (total_d * (i + 1)) // nreal
        while done_d < due:
            c = old_cls[rr % len(old_cls)]; rr += 1
            k = _dream(on, n, c, rng, buf)
            writes += _practise(W, buf, k, c, known, margin, cmax); done_d += 1
        tick += 1
        if tick % ch == 0:
            _follow(S, W, K)
    if len(old_cls) > 0:
        kn = np.where(known)[0]; blockw = 0; stop = False
        for p in range(night):
            for j in range(ndream * len(kn)):
                c = kn[j % len(kn)]
                k = _dream(on, n, c, rng, buf)
                w = _practise(W, buf, k, c, known, margin, cmax)
                writes += w; blockw += w; stats[0] += 1; stats[1] += w
                tick += 1
                if tick % ch == 0:
                    _follow(S, W, K)
                if night_stop > 0 and stats[0] % 256 == 0:
                    if blockw > night_stop:
                        stop = True
                        break
                    blockw = 0
            if stop:
                break
    return writes, tick


class CortexSlow(CortexInt):
    def __init__(self, n_bits, ch=500, K=3, small="copy", **kw):
        super().__init__(n_bits, **kw)
        self.ch, self.K, self.small = ch, K, small; self.S = np.zeros(self.W.shape, np.int32); self.tick = 0

    def stage(self, code, y):
        new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
        A, na = self.pack(code)
        r, self.tick = _stage_slow(self.W, self.S, self.on, self.n, self.rng, self.known, A, na, y.astype(np.int64), new, old.astype(np.int64),
                                   self.ndream, self.night, self.margin, self.cmax, self.top, self.daydream, self.night_stop, self.stats,
                                   self.ch, self.K, self.tick)
        if self.imprint:
            hit = [int(c) for c in new if 1 <= self.n[c] <= self.imprint_n]
            for c in new:
                self.imprint_class(int(c))
            if hit and self.imprint_sleep:
                from cortex_int import _practise as pr
                buf = np.zeros(self.W.shape[1], np.int32); kn = np.where(self.known)[0]
                for j in range(self.imprint_sleep * len(kn)):
                    c = kn[j % len(kn)]; k = _dream(self.on, self.n, c, self.rng, buf)
                    pr(self.W, buf, k, c, self.known, self.margin, self.cmax)
        if len(y) < 2 * self.ch:
            if self.small == "copy":
                self.S[:] = 16 * self.W.astype(np.int32)
            else:                                                             # "rows": only the new classes' rows are copied
                for c in new:
                    self.S[c] = 16 * self.W[c].astype(np.int32)
        return r

    def predict(self, code):
        s = code.astype(np.int32) @ self.S.T
        s[:, ~self.known] = -(1 << 30)
        return s.argmax(1)

    def memory_bits(self, B=10):
        d = super().memory_bits(B); d["slow_table"] = self.S.size * 8; return d
