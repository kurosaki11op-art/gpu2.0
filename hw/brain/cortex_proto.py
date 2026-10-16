"""Multi-prototype dreams (Redesign 4, 16 Oct 2026): the dream memory keeps K prototype count-sets per class instead of one,
so a dream keeps which features occur together. Integer only: adds, shifts, compares, the chip's xorshift lanes.

  * Learning an example of class c: the example goes to the prototype of c with the highest normalised overlap
        score_j = (sum over the example's active bits of on[c, j, bit]) << (10 - bitlen(n[c, j]))
    (a shift instead of a divide); an empty prototype wins first (the first K examples of a class seed the prototypes);
    the winner's counters are incremented (halved when its example count reaches the counter top, as for the class counters).
  * Dreaming class c: a prototype is drawn in proportion to its example count (lane 0 draw modulo the class total, compared
    with the running sum), then bits are drawn from that prototype's counters exactly like the single-set dream (L-bit
    random number compared with the counter).
The table, margin rule, day / night schedule, self-ending night and daydream are those of cortex_int._stage; only the dream
source differs. CortexProto subclasses CortexInt; the class-level counters on / n are kept as well (they are the sum of the
prototype counters up to halving and are used by IMPRINT). protos=1 reproduces CortexInt's dreams in structure (not bit for
bit: the random draws differ)."""
import numpy as np
from numba import njit
from cortex_int import CortexInt, _xs, _count, _practise, _dream


@njit(cache=True)
def _bitlen(v):
    L = 0
    while (1 << L) <= v:
        L += 1
    return L


@njit(cache=True)
def _assign(onp, nprot, c, K, act, na):
    """index (0..K-1) of the prototype of class c an example with active bits act[:na] goes to"""
    best = -1; bs = -1
    for j in range(K):
        r = c * K + j
        if nprot[r] == 0:
            return j
        s = 0
        for i in range(na):
            s += onp[r, act[i]]
        s = s << (10 - _bitlen(nprot[r])) if _bitlen(nprot[r]) <= 10 else s >> (_bitlen(nprot[r]) - 10)
        if s > bs:
            bs = s; best = j
    return best


@njit(cache=True)
def _observe(onp, nprot, c, K, act, na, top):
    j = _assign(onp, nprot, c, K, act, na)
    _count(onp, nprot, act, na, c * K + j, top)


@njit(cache=True)
def _dream_p(onp, nprot, c, K, rng, out):
    tot = 0
    for j in range(K):
        tot += nprot[c * K + j]
    if tot == 0:
        return 0
    rng[0] = _xs(rng[0]); r = np.int64(rng[0] % np.uint32(tot)); acc = 0; pick = 0
    for j in range(K):
        acc += nprot[c * K + j]
        if r < acc:
            pick = j; break
    return _dream(onp, nprot, c * K + pick, rng, out)


@njit(cache=True)
def _stage_p(W, on, n, onp, nprot, K, rng, known, acts, nacts, ys, new_cls, old_cls, ndream, night, margin, cmax, top,
             daydream, night_stop, stats):
    buf = np.zeros(on.shape[1], np.int32)
    for c in new_cls:
        known[c] = True
    nreal = len(ys); total_d = ndream * len(old_cls); done_d = 0; rr = 0; writes = 0
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
    if len(old_cls) > 0:
        kn = np.where(known)[0]; blockw = 0; stop = False
        for p in range(night):
            for j in range(ndream * len(kn)):
                c = kn[j % len(kn)]
                k = _dream_p(onp, nprot, c, K, rng, buf)
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


class CortexProto(CortexInt):
    def __init__(self, n_bits, protos=4, **kw):
        super().__init__(n_bits, **kw)
        self.K = protos
        self.onp = np.zeros((self.W.shape[0] * protos, n_bits), np.uint16)
        self.nprot = np.zeros(self.W.shape[0] * protos, np.int32)

    def stage(self, code, y):
        new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
        A, na = self.pack(code)
        return _stage_p(self.W, self.on, self.n, self.onp, self.nprot, self.K, self.rng, self.known, A, na, y.astype(np.int64),
                        new, old.astype(np.int64), self.ndream, self.night, self.margin, self.cmax, self.top, self.daydream,
                        self.night_stop, self.stats)

    def memory_bits(self, B=10):
        return {"fast_table": self.W.size * 5, "dream_counts": self.onp.size * B + self.nprot.size * B}
