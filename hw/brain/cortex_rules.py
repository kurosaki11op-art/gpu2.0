"""Our own learning-rule variants for the counting chip (20 Oct 2026). SIMULATED. Three brain-principled changes to how the fast table is trained, each local and integer (no multiply):
  grade:SH   graded surprise: when the rival outscores the right class by `wrong`, the write step is 1 + min(3, wrong >> SH) instead of 1 (a reward-error signal that is bigger for bigger errors; shifts only)
  budget:X   synaptic budget (heterosynaptic competition): after the day, a class whose total |weight| exceeds the mean over known classes by more than a fraction X (X in 1/16 units) loses its weakest synapses (|w| = 1 -> 0) until it is back under budget
  shy:1      night downscaling (synaptic homeostasis during sleep): before the night's dreams every nonzero fast-table weight steps one unit toward zero; the dreams then strengthen what is replayed
  split      control: the night run as a separate call with no change (must equal the shipped chip)
The day part is cortex_slow._stage_slow (built from its source for `grade`); `budget` / `shy` run the day with no night, apply their operation, then run the night alone."""
import inspect, re
import numpy as np
from numba import njit
import cortex_slow
from cortex_int import _scores
from cortex_slow import CortexSlow, _stage_slow


def make_stage_grade(sh):
    src = f'''
@njit
def _practise_g(W, act, na, y, known, margin, cmax):
    sc = _scores(W, act, na, known)
    t = sc[y]; rv = -1; best = -(1 << 30) - 1
    for c in range(W.shape[0]):
        if c != y and sc[c] > best:
            best = sc[c]; rv = c
    if rv < 0 or not known[rv] or t - best > margin:
        return 0
    wrong = best - t
    step = 1
    if wrong > 0:
        step = 1 + min(3, wrong >> {sh})
    for i in range(na):
        b = act[i]
        v = W[y, b] + step
        W[y, b] = cmax if v > cmax else v
        u = W[rv, b] - step
        W[rv, b] = -cmax if u < -cmax else u
    return 1
'''
    ns = dict(cortex_slow.__dict__); exec(src, ns | {"njit": njit, "_scores": _scores, "np": np}, ns)
    base = re.sub(r"^@njit\(cache=True\)\n", "", inspect.getsource(cortex_slow._stage_slow.py_func))
    stage = base.replace("def _stage_slow(", "def _stage_grade(").replace("_practise(W, ", "_practise_g(W, ")
    exec("@njit\n" + stage, ns); return ns["_stage_grade"]


class CortexRules(CortexSlow):
    def __init__(self, n_bits, rule="split", par=0, **kw):
        super().__init__(n_bits, **kw); self.rule, self.par = rule, par; self._night = kw.get("night", 2)
        self._stage_g = make_stage_grade(par) if rule == "grade" else None

    def _call(self, fn, code, y, night):
        new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
        A, na = self.pack(code)
        r, self.tick = fn(self.W, self.S, self.on, self.n, self.rng, self.known, A, na, y.astype(np.int64), new, old.astype(np.int64), self.ndream, night, self.margin,
                          self.cmax, self.top, self.daydream, self.night_stop, self.stats, self.ch, self.K, self.FR, self.RND, self.tick)
        return r

    def _night_only(self):
        old = np.where(self.known)[0].astype(np.int64)
        _, self.tick = _stage_slow(self.W, self.S, self.on, self.n, self.rng, self.known, np.zeros((0, 1), np.int32), np.zeros(0, np.int32), np.zeros(0, np.int64), np.zeros(0, np.int64), old,
                                   self.ndream, self._night, self.margin, self.cmax, self.top, self.daydream, self.night_stop, self.stats, self.ch, self.K, self.FR, self.RND, self.tick)

    def stage(self, code, y):
        if self.rule == "grade":
            r = self._call(self._stage_g, code, y, self._night)
        else:
            r = self._call(_stage_slow, code, y, 0)                         # the day, no night
            k = np.where(self.known)[0]
            if self.rule == "budget" and len(k) > 1:
                tot = np.abs(self.W[k].astype(np.int64)).sum(1); lim = int(tot.mean() * (16 + self.par) // 16)
                for c, t in zip(k, tot):
                    if t > lim:
                        ones = np.where(np.abs(self.W[c]) == 1)[0]; need = min(len(ones), int(t - lim)); self.W[c, ones[:need]] = 0
            if self.rule == "shy": self.W[:] = self.W - np.sign(self.W)
            if len(np.where(self.known)[0]) > len(np.unique(y)): self._night_only()
        if len(y) < 2 * self.ch: self.S[:] = self.W.astype(np.int32) << self.FR
        return r
