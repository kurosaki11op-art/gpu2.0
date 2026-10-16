"""Pool-limited multi-prototype dreams (Redesign 4b, 16 Oct 2026): like cortex_proto, but a class opens a new prototype only when no
existing prototype of that class overlaps the example well enough (spawn on novelty), and all classes share a fixed pool of P
prototype slots. Aim: keep most of the K=4..8 gain at about 2x the dream memory instead of 4-8x. Integer only.
  spawn when best normalised overlap < (na * 1024 * T) >> 4   (T in 0..16; na = number of active bits of the example)"""
import numpy as np
from numba import njit
from cortex_int import _count, _practise
from cortex_proto import CortexProto, _bitlen, _dream_p, _stage_p


@njit(cache=True)
def _assign_pool(onp, nprot, c, K, act, na, T, pool_used, P):
    best = -1; bs = -1; free = -1
    for j in range(K):
        r = c * K + j
        if nprot[r] == 0:
            free = j
            break
        s = 0
        for i in range(na):
            s += onp[r, act[i]]
        bl = _bitlen(nprot[r])
        s = s << (10 - bl) if bl <= 10 else s >> (bl - 10)
        if s > bs:
            bs = s; best = j
    if best < 0:
        pool_used[0] += 1
        return 0
    if free >= 0 and pool_used[0] < P and bs < ((na * 1024 * T) >> 4):
        pool_used[0] += 1
        return free
    return best


@njit(cache=True)
def _stage_pool(W, on, n, onp, nprot, K, rng, known, acts, nacts, ys, new_cls, old_cls, ndream, night, margin, cmax, top,
                daydream, night_stop, stats, T, pool_used, P):
    buf = np.zeros(on.shape[1], np.int32)
    for c in new_cls:
        known[c] = True
    nreal = len(ys); total_d = ndream * len(old_cls); done_d = 0; rr = 0; writes = 0
    for i in range(nreal):
        _count(on, n, acts[i], nacts[i], ys[i], top)
        j = _assign_pool(onp, nprot, ys[i], K, acts[i], nacts[i], T, pool_used, P)
        _count(onp, nprot, acts[i], nacts[i], ys[i] * K + j, top)
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


class CortexPool(CortexProto):
    def __init__(self, n_bits, pool=20, spawn=8, kmax=8, **kw):
        super().__init__(n_bits, protos=kmax, **kw)
        self.P = pool; self.T = spawn; self.pool_used = np.zeros(1, np.int64)

    def stage(self, code, y):
        new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
        A, na = self.pack(code)
        return _stage_pool(self.W, self.on, self.n, self.onp, self.nprot, self.K, self.rng, self.known, A, na, y.astype(np.int64),
                           new, old.astype(np.int64), self.ndream, self.night, self.margin, self.cmax, self.top, self.daydream,
                           self.night_stop, self.stats, self.T, self.pool_used, self.P)

    def memory_bits(self, B=10):
        used = int(self.pool_used[0])
        return {"fast_table": self.W.size * 5, "dream_counts": used * self.onp.shape[1] * B + used * B}
