"""Our own learning-rule variants for the counting chip (20 Oct 2026). SIMULATED. Three brain-principled changes to how the fast table is trained, each local and integer (no multiply):
  grade:SH   graded surprise: when the rival outscores the right class by `wrong`, the write step is 1 + min(3, wrong >> SH) instead of 1 (a reward-error signal that is bigger for bigger errors; shifts only)
  budget:X   synaptic budget (heterosynaptic competition): after the day, a class whose total |weight| exceeds the mean over known classes by more than a fraction X (X in 1/16 units) loses its weakest synapses (|w| = 1 -> 0) until it is back under budget
  shy:1      night downscaling (synaptic homeostasis during sleep): before the night's dreams every nonzero fast-table weight steps one unit toward zero; the dreams then strengthen what is replayed
  prio:B     our own: surprise-prioritised replay at night (blocks of B dreams; each class's share of the next block grows with the surprise writes its dreams caused in the last block)
  split      control: the night run as a separate call with no change (must equal the shipped chip)
The day part is cortex_slow._stage_slow (built from its source for `grade`); `budget` / `shy` run the day with no night, apply their operation, then run the night alone."""
import inspect, re
import numpy as np
from numba import njit
import cortex_slow
from cortex_int import _scores, _dream, _practise
from cortex_slow import CortexSlow, _stage_slow, _follow


@njit
def _xs32(s):
    s ^= (s << np.uint32(13)) & np.uint32(0xFFFFFFFF); s ^= s >> np.uint32(17); s ^= (s << np.uint32(5)) & np.uint32(0xFFFFFFFF); return s


@njit
def _night_prio(W, S, on, n, rng, known, total, margin, cmax, top, ch, K, FR, RND, tick0, block):
    """Surprise-prioritised night (replay biased to what was surprising): dreams come in blocks of `block`; the class of each dream is drawn with weight 1 + (surprise writes its dreams caused in the previous block),
    so classes whose dreams still change the table get more of the night; xorshift draws and adds only."""
    C = W.shape[0]; buf = np.zeros(on.shape[1], np.int32); prev = np.zeros(C, np.int64); cur = np.zeros(C, np.int64); tick = tick0; done = 0
    while done < total:
        wsum = 0
        for c in range(C):
            if known[c] and n[c] > 0: wsum += 1 + prev[c]
        for c in range(C): cur[c] = 0
        for j in range(block):
            if done >= total: break
            rng[0] = _xs32(rng[0]); r = np.int64(rng[0] % np.uint32(wsum)); acc = 0; pick = 0
            for c in range(C):
                if known[c] and n[c] > 0:
                    acc += 1 + prev[c]
                    if r < acc:
                        pick = c; break
            k = _dream(on, n, pick, rng, buf); w = _practise(W, buf, k, pick, known, margin, cmax); cur[pick] += w; done += 1; tick += 1
            if tick % ch == 0: _follow(S, W, K, FR, RND)
        for c in range(C): prev[c] = cur[c]
    return tick


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
            if len(np.where(self.known)[0]) > len(np.unique(y)):
                if self.rule == "prio":
                    kn = np.where(self.known)[0]; total = self.ndream * len(kn) * self._night
                    self.tick = _night_prio(self.W, self.S, self.on, self.n, self.rng, self.known, int(total), self.margin, self.cmax, self.top, self.ch, self.K, self.FR, self.RND, self.tick, int(self.par or 256))
                else: self._night_only()
        if len(y) < 2 * self.ch: self.S[:] = self.W.astype(np.int32) << self.FR
        return r
