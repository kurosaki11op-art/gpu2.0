"""Group-structured dreams (Redesign 7, 18 Oct 2026). Finding (staged_diag.py): in staged learning the classes of the last stage, trained on REAL
examples, win test images of older classes that were only dreamed (clothing: 7->9 +21 points, 6->8 +10). The independent-bit dream breaks the
code's structure: the code is a one-of-F winner map per (position, channel) group (OR-pooled, at most POOL*POOL = 4 on bits per group), but an
independent draw can switch on any number of bits in a group. Here the dream keeps the structure:
  mode 1: after the independent draw, a group with more than cap on bits keeps only its cap bits with the largest counters;
  mode 2: as mode 1, plus a group with no on bit whose counters sum to at least n/2 (mostly active in this class) gets one bit by roulette
          over its counters (a masked random draw below the group's counter sum, then a cumulative walk).
Compares, adds and the chip's random lanes only. CortexGroup subclasses CortexInt; only the stage loop differs (night, daydream, margin same)."""
import numpy as np
from numba import njit
from cortex_int import CortexInt, _xs, _count, _practise, _dream


@njit(cache=True)
def _dream_g(on, n, c, rng, out, gF, cap, mode):
    k0 = _dream(on, n, c, rng, out)
    if mode == 0 or k0 == 0:
        return k0
    nb = on.shape[1]; ng = nb // gF; k = 0; i = 0
    res = np.empty(nb, np.int32); keep = np.empty(gF, np.int32)
    for g in range(ng):
        lo = g * gF; hi = lo + gF; j0 = i
        while i < k0 and out[i] < hi:
            i += 1
        cnt = i - j0
        if cnt > cap:                                   # keep the cap bits with the largest counters
            for q in range(j0, i):
                keep[q - j0] = out[q]
            for t in range(cap):
                bi = -1; bv = -1
                for q in range(cnt):
                    if keep[q] >= 0 and on[c, keep[q]] > bv:
                        bv = on[c, keep[q]]; bi = q
                res[k + t] = keep[bi]; keep[bi] = -1
            for a in range(1, cap):                      # sort the kept bits ascending
                v = res[k + a]; q = a - 1
                while q >= 0 and res[k + q] > v:
                    res[k + q + 1] = res[k + q]; q -= 1
                res[k + q + 1] = v
            k += cap
        elif cnt == 0:
            if mode == 2:
                tot = 0
                for b in range(lo, hi):
                    tot += on[c, b]
                if tot > 0 and tot * 2 >= n[c]:
                    Lg = 0
                    while (1 << Lg) <= tot:
                        Lg += 1
                    mask = np.uint32((1 << Lg) - 1); lane = g % 32
                    while True:
                        rng[lane] = _xs(rng[lane]); r = np.int64(rng[lane] & mask)
                        if r < tot:
                            break
                    acc = 0
                    for b in range(lo, hi):
                        acc += on[c, b]
                        if r < acc:
                            res[k] = b; k += 1
                            break
        else:
            for q in range(j0, i):
                res[k] = out[q]; k += 1
    for q in range(k):
        out[q] = res[q]
    return k


@njit(cache=True)
def _stage_g(W, on, n, rng, known, acts, nacts, ys, new_cls, old_cls, ndream, night, margin, cmax, top, daydream, replay_k,
           night_stop, stats, fon, fn, use_f, gF, cap, mode):
    """one stage: day (real examples once, dreams of old classes interleaved), then night.
    daydream: after each real example, practise this many dreams of the example's own class (new-class daydreams).
    replay_k: short-term buffer of the last replay_k examples; after each real example one buffered example (chosen by
    the lane-0 random generator) is practised again.
    night_stop: self-regulated night (0 = off). The night runs in blocks of 256 dreams and ends after a block in which
    more than night_stop out of 256 dreams surprised the table (dreams disagree with what real days taught).
    stats[0] = night dreams run, stats[1] = night writes.
    use_f (context memory): the day brings classes already known; old_cls then lists every class known before the day,
    and their day dreams come from the frozen copy (fon, fn) of the dream counts taken before the day; at night, dreams
    alternate between the live counts and the frozen copy."""
    buf = np.zeros(on.shape[1], np.int32)
    for c in new_cls:
        known[c] = True
    nreal = len(ys); total_d = ndream * len(old_cls); done_d = 0; rr = 0; writes = 0
    for i in range(nreal):
        _count(on, n, acts[i], nacts[i], ys[i], top)
        writes += _practise(W, acts[i], nacts[i], ys[i], known, margin, cmax)
        for d in range(daydream):
            k = _dream_g(on, n, ys[i], rng, buf, gF, cap, mode)
            writes += _practise(W, buf, k, ys[i], known, margin, cmax)
        if replay_k > 0 and i > 0:
            rng[0] = _xs(rng[0]); lo = max(0, i - replay_k); j = lo + int(rng[0] % np.uint32(i - lo))
            writes += _practise(W, acts[j], nacts[j], ys[j], known, margin, cmax)
        due = (total_d * (i + 1)) // nreal                                  # dreams owed by now (integer ratio)
        while done_d < due:
            c = old_cls[rr % len(old_cls)]; rr += 1
            k = _dream_g(fon, fn, c, rng, buf, gF, cap, mode) if use_f else _dream_g(on, n, c, rng, buf, gF, cap, mode)
            writes += _practise(W, buf, k, c, known, margin, cmax); done_d += 1
    if len(old_cls) > 0:
        kn = np.where(known)[0]; blockw = 0; stop = False
        for p in range(night):
            for j in range(ndream * len(kn)):
                c = kn[j % len(kn)]
                if use_f and (j // len(kn)) % 2 == 1:
                    k = _dream_g(fon, fn, c, rng, buf, gF, cap, mode)
                else:
                    k = _dream_g(on, n, c, rng, buf, gF, cap, mode)
                w = _practise(W, buf, k, c, known, margin, cmax)
                writes += w; blockw += w; stats[0] += 1; stats[1] += w
                if night_stop > 0 and stats[0] % 256 == 0:
                    if blockw > night_stop:
                        stop = True
                        break
                    blockw = 0
            if stop:
                break
    return writes


class CortexGroup(CortexInt):
    def __init__(self, n_bits, gF=32, cap=4, mode=1, **kw):
        super().__init__(n_bits, **kw)
        self.gF, self.cap, self.mode = gF, cap, mode

    def stage(self, code, y):
        new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
        fon, fn = self.on.copy(), self.n.copy()
        A, na = self.pack(code)
        return _stage_g(self.W, self.on, self.n, self.rng, self.known, A, na, y.astype(np.int64), new, old.astype(np.int64),
                        self.ndream, self.night, self.margin, self.cmax, self.top, self.daydream, self.replay_k,
                        self.night_stop, self.stats, fon, fn, False, self.gF, self.cap, self.mode)
