"""Chip model with noisy night dreams (21 Oct 2026): night dreams drop each active bit with probability 2^-drop and add (len >> add) random bits; day dreams stay clean. Integer, xorshift only. SIMULATED."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
import numpy as np
from cortex_int import _practise, _count, _xs
from cortex_slow import CortexSlow, _follow
try:
    from numba import njit
except ImportError:
    def njit(*a, **k): return (lambda f: f) if not (a and callable(a[0])) else a[0]

@njit(cache=True)
def _dream_noisy(on, n, c, rng, out, drop, add):
    """cortex_int._dream, then: drop each active bit with probability 2^-drop (0 = none), then add (len >> add) random bits (0 = none). xorshift draws only."""
    nb = on.shape[1]; nc = n[c]
    if nc == 0: return 0
    L = 0
    while (1 << L) <= nc: L += 1
    mask = np.uint32((1 << L) - 1); k = 0
    for b in range(nb):
        lane = b % 32
        while True:
            rng[lane] = _xs(rng[lane]); r = rng[lane] & mask
            if r < nc: break
        if r < on[c, b]:
            keep = True
            if drop > 0:
                rng[lane] = _xs(rng[lane])
                if (rng[lane] & np.uint32((1 << drop) - 1)) == 0: keep = False
            if keep:
                out[k] = b; k += 1
    if add > 0:
        extra = k >> add
        for j in range(extra):
            rng[j % 32] = _xs(rng[j % 32]); out[k] = rng[j % 32] % nb; k += 1
    return k

@njit(cache=True)
def _stage_nd(W, S, on, n, rng, known, acts, nacts, ys, new_cls, old_cls, ndream, night, margin, cmax, top, daydream, night_stop, stats, ch, K, FR, RND, tick0, drop, add):
    """cortex_slow._stage_slow with noisy night dreams (day and daydreams stay clean)."""
    buf = np.zeros(on.shape[1] + on.shape[1] // 2 + 8, np.int32)
    for c in new_cls: known[c] = True
    nreal = len(ys); total_d = ndream * len(old_cls); done_d = 0; rr = 0; writes = 0; tick = tick0
    from_dream = 0
    for i in range(nreal):
        _count(on, n, acts[i], nacts[i], ys[i], top)
        writes += _practise(W, acts[i], nacts[i], ys[i], known, margin, cmax)
        for d in range(daydream):
            k = _dream_noisy(on, n, ys[i], rng, buf, 0, 0)
            writes += _practise(W, buf, k, ys[i], known, margin, cmax)
        due = (total_d * (i + 1)) // nreal
        while done_d < due:
            c = old_cls[rr % len(old_cls)]; rr += 1
            k = _dream_noisy(on, n, c, rng, buf, 0, 0)
            writes += _practise(W, buf, k, c, known, margin, cmax); done_d += 1
        tick += 1
        if tick % ch == 0: _follow(S, W, K, FR, RND)
    if len(old_cls) > 0:
        kn = np.where(known)[0]; blockw = 0; stop = False
        for p in range(night):
            for j in range(ndream * len(kn)):
                c = kn[j % len(kn)]
                k = _dream_noisy(on, n, c, rng, buf, drop, add)
                w = _practise(W, buf, k, c, known, margin, cmax)
                writes += w; blockw += w; stats[0] += 1; stats[1] += w
                tick += 1
                if tick % ch == 0: _follow(S, W, K, FR, RND)
                if night_stop > 0 and stats[0] % 256 == 0:
                    if blockw > night_stop: stop = True; break
                    blockw = 0
            if stop: break
    return writes, tick

class NoisyDreamChip(CortexSlow):
    def __init__(self, n_bits, drop=0, add=0, **kw):
        super().__init__(n_bits, **kw); self.drop, self.add = drop, add
    def stage(self, code, y):
        new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
        A, na = self.pack(code)
        r, self.tick = _stage_nd(self.W, self.S, self.on, self.n, self.rng, self.known, A, na, y.astype(np.int64), new, old.astype(np.int64), self.ndream, self.night, self.margin,
                                 self.cmax, self.top, self.daydream, self.night_stop, self.stats, self.ch, self.K, self.FR, self.RND, self.tick, self.drop, self.add)
        if len(y) < 2 * self.ch: self.S[:] = self.W.astype(np.int32) << self.FR
        return r

