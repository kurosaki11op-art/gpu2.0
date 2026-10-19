"""Cascade synapses (metaplasticity), 19 Oct 2026. SIMULATED. Brain principle: a synapse that keeps being pushed the same way becomes harder to change (Fusi-style hidden states).
Each fast-table synapse W[c, b] gets a consolidation level H (0..HMAX) and the direction D of its last change. A write is applied with probability 2^-H (an xorshift draw masked by 2^H - 1, so shifts and compares only);
when applied: same direction as last time -> H + 1 (up to HMAX), opposite direction -> H = 0. Everything else is the slow-table chip (cortex_slow). Extra memory: 3 bits per synapse (HMAX 3 = 2 bits + 1 direction bit).
The stage loop is cortex_slow._stage_slow with _practise replaced, built from its source so the two cannot drift apart."""
import inspect, re
import numpy as np
from numba import njit
import cortex_slow
from cortex_int import _scores, _xs
from cortex_slow import CortexSlow


@njit(cache=True)
def _practise_c(W, H, D, rng, hmax, act, na, y, known, margin, cmax):
    sc = _scores(W, act, na, known)
    t = sc[y]; rv = -1; best = -(1 << 30) - 1
    for c in range(W.shape[0]):
        if c != y and sc[c] > best:
            best = sc[c]; rv = c
    if rv < 0 or not known[rv] or t - best > margin:
        return 0
    for i in range(na):
        b = act[i]
        for k in range(2):
            c = y if k == 0 else rv; d = 1 if k == 0 else -1
            if (d > 0 and W[c, b] >= cmax) or (d < 0 and W[c, b] <= -cmax):
                continue
            h = H[c, b]; lane = (b + c) % 32; rng[lane] = _xs(rng[lane])
            if (rng[lane] & np.uint32((1 << h) - 1)) != 0:
                continue
            W[c, b] += d
            if D[c, b] == d:
                if h < hmax: H[c, b] = h + 1
            else:
                D[c, b] = d; H[c, b] = 0
    return 1


_src = inspect.getsource(cortex_slow._stage_slow.py_func)
_src = _src.replace("def _stage_slow(W, S,", "def _stage_casc(H, D, hmax, W, S,").replace("_practise(W, ", "_practise_c(W, H, D, rng, hmax, ")
_src = re.sub(r"^@njit\(cache=True\)\n", "", _src)
_ns = dict(cortex_slow.__dict__); _ns.update(_practise_c=_practise_c)
exec(compile("@njit\n" + _src, "cortex_casc_stage", "exec"), _ns)
_stage_casc = _ns["_stage_casc"]


class CortexCasc(CortexSlow):
    def __init__(self, n_bits, hmax=3, **kw):
        super().__init__(n_bits, **kw)
        self.hmax = hmax; self.H = np.zeros(self.W.shape, np.int8); self.D = np.zeros(self.W.shape, np.int8)

    def stage(self, code, y):
        new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
        A, na = self.pack(code)
        r, self.tick = _stage_casc(self.H, self.D, self.hmax, self.W, self.S, self.on, self.n, self.rng, self.known, A, na, y.astype(np.int64), new, old.astype(np.int64),
                                   self.ndream, self.night, self.margin, self.cmax, self.top, self.daydream, self.night_stop, self.stats,
                                   self.ch, self.K, self.FR, self.RND, self.tick)
        if len(y) < 2 * self.ch: self.S[:] = self.W.astype(np.int32) << self.FR
        return r

    def memory_bits(self, B=10):
        d = super().memory_bits(B); d["cascade_state"] = self.W.size * 3; return d
