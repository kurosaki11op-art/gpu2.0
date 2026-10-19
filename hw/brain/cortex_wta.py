"""Dreams with lateral inhibition (19 Oct 2026). SIMULATED. Brain principle: during replay the same lateral competition that shapes sensing limits how many features fire at one place.
A sensed code has at most 4 features per pooled spot (2 x 2 pooling of one winner per window); a dream that draws every bit independently can fire many more. Here the dream is drawn as before, then at each spot
(a block of F = 32 consecutive bits) only the KW drawn bits with the largest dream counts on[c, b] stay (compare and select only, no extra memory). Stage loop = cortex_slow._stage_slow built from its source
with _dream replaced; the daydreams and the night use the same dream."""
import inspect, re
import numpy as np
from numba import njit
import cortex_slow
from cortex_int import _xs
from cortex_slow import CortexSlow


def make_dream(kw, F=32):
    src = f'''
@njit
def _dream_w(on, n, c, rng, out):
    nb = on.shape[1]; nc = n[c]
    if nc == 0:
        return 0
    L = 0
    while (1 << L) <= nc:
        L += 1
    mask = np.uint32((1 << L) - 1); k = 0; blk = 0
    for b in range(nb):
        lane = b % 32
        while True:
            rng[lane] = _xs(rng[lane]); r = rng[lane] & mask
            if r < nc:
                break
        if r < on[c, b]:
            out[k] = b; k += 1
        if (b + 1) % {F} == 0:
            m = k - blk
            while m > {kw}:                                    # lateral inhibition: drop the weakest drawn bit of this spot
                wj = blk; wv = on[c, out[blk]]
                for j in range(blk + 1, k):
                    if on[c, out[j]] < wv:
                        wv = on[c, out[j]]; wj = j
                out[wj] = out[k - 1]; k -= 1; m -= 1
            blk = k
    return k
'''
    ns = {"njit": njit, "np": np, "_xs": _xs}; exec(src, ns); return ns["_dream_w"]


_base = inspect.getsource(cortex_slow._stage_slow.py_func)
_base = re.sub(r"^@njit\(cache=True\)\n", "", _base)


def make_stage(kw):
    ns = dict(cortex_slow.__dict__); ns["_dream_w"] = make_dream(kw)
    src = _base.replace("def _stage_slow(", "def _stage_wta(").replace("_dream(", "_dream_w(")
    exec("@njit\n" + src, ns); return ns["_stage_wta"]


class CortexWTA(CortexSlow):
    def __init__(self, n_bits, kw=4, **kw_):
        super().__init__(n_bits, **kw_); self._stage = make_stage(kw)

    def stage(self, code, y):
        new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
        A, na = self.pack(code)
        r, self.tick = self._stage(self.W, self.S, self.on, self.n, self.rng, self.known, A, na, y.astype(np.int64), new, old.astype(np.int64),
                                   self.ndream, self.night, self.margin, self.cmax, self.top, self.daydream, self.night_stop, self.stats,
                                   self.ch, self.K, self.FR, self.RND, self.tick)
        if len(y) < 2 * self.ch: self.S[:] = self.W.astype(np.int32) << self.FR
        return r
