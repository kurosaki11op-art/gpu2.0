"""Separate (larger) margin for dreams (Redesign 9 test, 18 Oct 2026): real examples keep the margin rule (margin), dreams are practised against dmargin.
Idea: dreams of old classes are easy (they pass the margin test and teach nothing), while the real examples of the new classes push the old rows down; a larger margin
on dreams makes the old rows win by more on their own dreams. CortexDM subclasses CortexInt; only the dream margin differs."""
import numpy as np
from numba import njit
from cortex_int import CortexInt, _xs, _count, _practise, _dream


@njit(cache=True)
def _stage_dm(W, on, n, rng, known, acts, nacts, ys, new_cls, old_cls, ndream, night, margin, cmax, top, daydream, replay_k,
           night_stop, stats, fon, fn, use_f, dmargin):
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
            k = _dream(on, n, ys[i], rng, buf)
            writes += _practise(W, buf, k, ys[i], known, dmargin, cmax)
        if replay_k > 0 and i > 0:
            rng[0] = _xs(rng[0]); lo = max(0, i - replay_k); j = lo + int(rng[0] % np.uint32(i - lo))
            writes += _practise(W, acts[j], nacts[j], ys[j], known, margin, cmax)
        due = (total_d * (i + 1)) // nreal                                  # dreams owed by now (integer ratio)
        while done_d < due:
            c = old_cls[rr % len(old_cls)]; rr += 1
            k = _dream(fon, fn, c, rng, buf) if use_f else _dream(on, n, c, rng, buf)
            writes += _practise(W, buf, k, c, known, dmargin, cmax); done_d += 1
    if len(old_cls) > 0:
        kn = np.where(known)[0]; blockw = 0; stop = False
        for p in range(night):
            for j in range(ndream * len(kn)):
                c = kn[j % len(kn)]
                if use_f and (j // len(kn)) % 2 == 1:
                    k = _dream(fon, fn, c, rng, buf)
                else:
                    k = _dream(on, n, c, rng, buf)
                w = _practise(W, buf, k, c, known, dmargin, cmax)
                writes += w; blockw += w; stats[0] += 1; stats[1] += w
                if night_stop > 0 and stats[0] % 256 == 0:
                    if blockw > night_stop:
                        stop = True
                        break
                    blockw = 0
            if stop:
                break
    return writes


class CortexDM(CortexInt):
    def __init__(self, n_bits, dmargin=64, **kw):
        super().__init__(n_bits, **kw)
        self.dmargin = dmargin

    def stage(self, code, y):
        new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
        fon, fn = self.on.copy(), self.n.copy()
        A, na = self.pack(code)
        return _stage_dm(self.W, self.on, self.n, self.rng, self.known, A, na, y.astype(np.int64), new, old.astype(np.int64),
                         self.ndream, self.night, self.margin, self.cmax, self.top, self.daydream, self.replay_k,
                         self.night_stop, self.stats, fon, fn, False, self.dmargin)
