"""SPARK Cortex integer reference model (month 3): the exact behaviour the RTL must match, bit for bit.

Integers only: no floating point, no multiplies, no divides. Every example is processed once, in order, the way a
streaming chip sees it.

State
  W   [10, NB] int8   fast table, signed counters saturating at +-CMAX (5-bit: CMAX = 15)
  on  [10, NB] uint16 dream memory: per class, how often each code bit fired (B-bit, synaptic scaling)
  n   [10]     int32  per class example count (B-bit); when it reaches 2^B - 1, on[c] and n[c] are halved
  rng [32]     uint32 xorshift32 random generators, one per lane

Operations
  decide(active)      : score[c] = sum of W[c, b] over active bits b; answer = first class with the top score
                        among known classes
  practise(active, y) : if score[y] - best rival <= MARGIN: W[y, active] += 1, W[rival, active] -= 1 (saturating)
  count(active, y)    : on[y, active] += 1; n[y] += 1; halve when full
  dream(c)            : code bit b uses lane b % 32; that lane draws r = rng & (2^L - 1) with L = bit length of n[c],
                        redrawing while r >= n[c]; the bit is on if r < on[c, b]
Schedule per stage (classes new to this stage = the day's experiences)
  day   : for each real example: count, practise; then practise on dreams of old classes, interleaved so that over the
          day each old class gets NDREAM dreams (round robin over old classes)
  night : if there are old classes, NIGHT passes; each pass practises NDREAM dreams of every known class, round robin"""
import numpy as np
from numba import njit

LANES = 32


@njit(cache=True)
def _xs(s):
    s ^= (s << np.uint32(13)) & np.uint32(0xFFFFFFFF)
    s ^= s >> np.uint32(17)
    s ^= (s << np.uint32(5)) & np.uint32(0xFFFFFFFF)
    return s


@njit(cache=True)
def _scores(W, act, na, known):
    C = W.shape[0]; sc = np.zeros(C, np.int32)
    for c in range(C):
        t = 0
        for i in range(na):
            t += W[c, act[i]]
        sc[c] = t if known[c] else -(1 << 30)
    return sc


@njit(cache=True)
def _practise(W, act, na, y, known, margin, cmax):
    sc = _scores(W, act, na, known)
    t = sc[y]; rv = -1; best = -(1 << 30) - 1
    for c in range(W.shape[0]):
        if c != y and sc[c] > best:
            best = sc[c]; rv = c
    if rv < 0 or not known[rv] or t - best > margin:
        return 0
    for i in range(na):
        b = act[i]
        if W[y, b] < cmax:
            W[y, b] += 1
        if W[rv, b] > -cmax:
            W[rv, b] -= 1
    return 1


@njit(cache=True)
def _count(on, n, act, na, y, top):
    for i in range(na):
        on[y, act[i]] += 1
    n[y] += 1
    if n[y] >= top:
        for b in range(on.shape[1]):
            on[y, b] >>= 1
        n[y] >>= 1


@njit(cache=True)
def _dream(on, n, c, rng, out):
    nb = on.shape[1]; nc = n[c]
    L = 0
    while (1 << L) <= nc:
        L += 1
    mask = np.uint32((1 << L) - 1); k = 0
    for b in range(nb):
        lane = b % 32
        while True:
            rng[lane] = _xs(rng[lane]); r = rng[lane] & mask
            if r < nc:
                break
        if r < on[c, b]:
            out[k] = b; k += 1
    return k


@njit(cache=True)
def _stage(W, on, n, rng, known, acts, nacts, ys, new_cls, old_cls, ndream, night, margin, cmax, top, daydream, replay_k):
    """one stage: day (real examples once, dreams of old classes interleaved), then night.
    daydream: after each real example, practise this many dreams of the example's own class (new-class daydreams).
    replay_k: short-term buffer of the last replay_k examples; after each real example one buffered example (chosen by
    the lane-0 random generator) is practised again."""
    buf = np.zeros(on.shape[1], np.int32)
    for c in new_cls:
        known[c] = True
    nreal = len(ys); total_d = ndream * len(old_cls); done_d = 0; rr = 0; writes = 0
    for i in range(nreal):
        _count(on, n, acts[i], nacts[i], ys[i], top)
        writes += _practise(W, acts[i], nacts[i], ys[i], known, margin, cmax)
        for d in range(daydream):
            k = _dream(on, n, ys[i], rng, buf)
            writes += _practise(W, buf, k, ys[i], known, margin, cmax)
        if replay_k > 0 and i > 0:
            rng[0] = _xs(rng[0]); lo = max(0, i - replay_k); j = lo + int(rng[0] % np.uint32(i - lo))
            writes += _practise(W, acts[j], nacts[j], ys[j], known, margin, cmax)
        due = (total_d * (i + 1)) // nreal                                  # dreams owed by now (integer ratio)
        while done_d < due:
            c = old_cls[rr % len(old_cls)]; rr += 1
            k = _dream(on, n, c, rng, buf)
            writes += _practise(W, buf, k, c, known, margin, cmax); done_d += 1
    if len(old_cls) > 0:
        kn = np.where(known)[0]
        for p in range(night):
            for j in range(ndream * len(kn)):
                c = kn[j % len(kn)]
                k = _dream(on, n, c, rng, buf)
                writes += _practise(W, buf, k, c, known, margin, cmax)
    return writes


class CortexInt:
    def __init__(self, n_bits, n_cls=10, cmax=15, margin=8, B=10, ndream=6000, night=2, seed=1, daydream=0, replay_k=0):
        self.W = np.zeros((n_cls, n_bits), np.int8); self.on = np.zeros((n_cls, n_bits), np.uint16)
        self.n = np.zeros(n_cls, np.int32); self.known = np.zeros(n_cls, np.bool_)
        self.rng = np.array([(0x9E3779B9 * (i + seed)) & 0xFFFFFFFF or 1 for i in range(LANES)], np.uint32)
        self.cmax, self.margin, self.top, self.ndream, self.night = cmax, margin, (1 << B) - 1, ndream, night
        self.daydream, self.replay_k = daydream, replay_k

    @staticmethod
    def pack(code):
        """bool codes (N, NB) -> padded active-index array and counts"""
        na = code.sum(1).astype(np.int32); A = np.zeros((len(code), max(1, na.max())), np.int32)
        for i, row in enumerate(code):
            idx = np.nonzero(row)[0]; A[i, :len(idx)] = idx
        return A, na

    def stage(self, code, y):
        new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
        A, na = self.pack(code)
        return _stage(self.W, self.on, self.n, self.rng, self.known, A, na, y.astype(np.int64), new, old.astype(np.int64),
                      self.ndream, self.night, self.margin, self.cmax, self.top, self.daydream, self.replay_k)

    def predict(self, code):
        s = code.astype(np.int32) @ self.W.T.astype(np.int32)                 # exact integer sums of table entries
        s[:, ~self.known] = -(1 << 30)
        return s.argmax(1)

    def memory_bits(self, B=10):
        return {"fast_table": self.W.size * 5, "dream_counts": self.on.size * B + self.n.size * B}
