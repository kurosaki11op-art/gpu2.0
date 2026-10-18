"""Multi-prototype dreams (cortex_proto.py) together with the slow table (cortex_slow.py): K prototypes per class for the dreams, S follows W every
CH ticks, prediction reads S. Redesign 4 + 6 combined (18 Oct 2026). CortexProtoSlow subclasses CortexProto."""
import numpy as np
from numba import njit
from cortex_int import _xs, _count, _practise, _dream
from cortex_proto import CortexProto, _observe, _dream_p
from cortex_slow import _follow


@njit(cache=True)
def _stage_ps(W, on, n, onp, nprot, K, rng, known, acts, nacts, ys, new_cls, old_cls, ndream, night, margin, cmax, top,
             daydream, night_stop, stats, S, ch, SK, FR, RND, tick0):
    buf = np.zeros(on.shape[1], np.int32)
    for c in new_cls:
        known[c] = True
    nreal = len(ys); total_d = ndream * len(old_cls); done_d = 0; rr = 0; writes = 0; tick = tick0
    for i in range(nreal):
        _count(on, n, acts[i], nacts[i], ys[i], top)
        _observe(onp, nprot, ys[i], K, acts[i], nacts[i], top)
        writes += _practise(W, acts[i], nacts[i], ys[i], known, margin, cmax)
        for d in range(daydream):
            k = _dream_p(onp, nprot, ys[i], K, rng, buf)
            writes += _practise(W, buf, k, ys[i], known, margin, cmax)
        due = (total_d * (i + 1)) // nreal
        while done_d < due:
            c = old_cls[rr % len(old_cls)]; rr += 1
            k = _dream_p(onp, nprot, c, K, rng, buf)
            writes += _practise(W, buf, k, c, known, margin, cmax); done_d += 1
        tick += 1
        if tick % ch == 0:
            _follow(S, W, SK, FR, RND)
    if len(old_cls) > 0:
        kn = np.where(known)[0]; blockw = 0; stop = False
        for p in range(night):
            for j in range(ndream * len(kn)):
                c = kn[j % len(kn)]
                k = _dream_p(onp, nprot, c, K, rng, buf)
                w = _practise(W, buf, k, c, known, margin, cmax)
                writes += w; blockw += w; stats[0] += 1; stats[1] += w
                tick += 1
                if tick % ch == 0:
                    _follow(S, W, SK, FR, RND)
                if night_stop > 0 and stats[0] % 256 == 0:
                    if blockw > night_stop:
                        stop = True
                        break
                    blockw = 0
            if stop:
                break
    return writes, tick


class CortexProtoSlow(CortexProto):
    def __init__(self, n_bits, protos=2, ch=500, K=3, FR=3, rnd=1, small="copy", **kw):
        super().__init__(n_bits, protos=protos, **kw)
        self.ch, self.SK, self.FR, self.small = ch, K, FR, small; self.RND = (1 << (K - 1)) if rnd else 0; self.S = np.zeros(self.W.shape, np.int32); self.tick = 0

    def stage(self, code, y):
        new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
        A, na = self.pack(code)
        r, self.tick = _stage_ps(self.W, self.on, self.n, self.onp, self.nprot, self.K, self.rng, self.known, A, na, y.astype(np.int64),
                                 new, old.astype(np.int64), self.ndream, self.night, self.margin, self.cmax, self.top, self.daydream,
                                 self.night_stop, self.stats, self.S, self.ch, self.SK, self.FR, self.RND, self.tick)
        if len(y) < 2 * self.ch:
            self.S[:] = self.W.astype(np.int32) << self.FR
        return r

    def predict(self, code):
        s = code.astype(np.int32) @ self.S.T
        s[:, ~self.known] = -(1 << 30)
        return s.argmax(1)
