"""Our own learning-rule variants for the counting chip (20 Oct 2026). SIMULATED. Three brain-principled changes to how the fast table is trained, each local and integer (no multiply):
  grade:SH   graded surprise: when the rival outscores the right class by `wrong`, the write step is 1 + min(3, wrong >> SH) instead of 1 (a reward-error signal that is bigger for bigger errors; shifts only)
  budget:X   synaptic budget (heterosynaptic competition): after the day, a class whose total |weight| exceeds the mean over known classes by more than a fraction X (X in 1/16 units) loses its weakest synapses (|w| = 1 -> 0) until it is back under budget
  shy:1      night downscaling (synaptic homeostasis during sleep): before the night's dreams every nonzero fast-table weight steps one unit toward zero; the dreams then strengthen what is replayed
  prio:B     our own: surprise-prioritised replay at night (blocks of B dreams; each class's share of the next block grows with the surprise writes its dreams caused in the last block)
  split      control: the night run as a separate call with no change (must equal the shipped chip)
The day part is cortex_slow._stage_slow (built from its source for `grade`); `budget` / `shy` run the day with no night, apply their operation, then run the night alone."""
import inspect, os, re
import numpy as np
from numba import njit
import cortex_slow
from cortex_int import _scores, _dream, _practise, _xs
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


@njit
def _night_real(W, S, on, n, rng, known, st, stn, stc, total, mixc, drop, rmargin, margin, cmax, top, ch, K, FR, RND, tick0, night_stop, stats):
    """Night with a few stored real traces per class (hippocampal-style index): each replay is, with probability mix/16, one of the class's stored real codes, otherwise an independent-bit dream.
    Class order is round robin; xorshift draws only."""
    C = W.shape[0]; buf = np.zeros(on.shape[1], np.int32); kn = np.where(known)[0]; tick = tick0; blockw = 0
    for j in range(total):
        c = kn[j % len(kn)]; rng[0] = _xs32(rng[0]); r = rng[0]; isreal = False
        if stc[c] > 0 and np.int64(r & np.uint32(15)) < mixc[c]:
            isreal = True; q = np.int64((r >> np.uint32(4)) % np.uint32(stc[c])); na = stn[c, q]
            k = 0
            for t in range(na):
                if drop > 0:
                    rng[0] = _xs32(rng[0])
                    if (rng[0] >> np.uint32(7)) % np.uint32(1 << drop) == 0: continue      # drop a stored bit with probability 2^-drop (a noisy copy of the stored trace)
                buf[k] = st[c, q, t]; k += 1
        else:
            k = _dream(on, n, c, rng, buf)
        w = _practise(W, buf, k, c, known, rmargin if isreal else margin, cmax); blockw += w; stats[0] += 1; stats[1] += w; tick += 1
        if tick % ch == 0: _follow(S, W, K, FR, RND)
        if night_stop > 0 and stats[0] % 256 == 0:
            if blockw > night_stop: break
            blockw = 0
    return tick


@njit
def _dreamx(on, n, st, stc, blk, mixp, c, rng, out):
    """cut-and-paste dream (replay recombines fragments of stored experience): with probability mixp/16 each block of `blk` code bits (one spatial cell) is copied from a randomly chosen one of the class's few stored real traces; otherwise the usual independent-bit dream.
    xorshift draws, copies and compares only."""
    rng[0] = _xs32(rng[0])
    if stc[c] == 0 or np.int64(rng[0] & np.uint32(15)) >= mixp:
        return _dream(on, n, c, rng, out)
    nb = on.shape[1]; k = 0
    for bs in range(0, nb, blk):
        rng[0] = _xs32(rng[0]); q = np.int64(rng[0] % np.uint32(stc[c]))
        for t in range(blk):
            if st[c, q, bs + t]:
                out[k] = bs + t; k += 1
    return k


@njit
def _dreamc(on, n, st, stc, blk, mixp, c, rng, out):
    """categorical dream: a real code has, in every spatial cell (block of `blk` bits), a small number of winning detectors, not a scatter of independent bits. Per block the expected number of winners is the sum of that block's on-counts over the class count (integer part plus one more with the fractional probability); that many distinct detectors are drawn with probability proportional to their on-counts. Same counts, no extra memory; xorshift draws, adds, compares."""
    nc = n[c]; nb = on.shape[1]; k = 0
    if nc == 0:
        return 0
    rng[0] = _xs32(rng[0])
    if np.int64(rng[0] & np.uint32(15)) >= mixp:
        return _dream(on, n, c, rng, out)
    for bs in range(0, nb, blk):
        tot = 0
        for t in range(blk): tot += on[c, bs + t]
        if tot == 0: continue
        cnt = tot // nc; rem = tot - cnt * nc; rng[0] = _xs32(rng[0])
        if np.int64(rng[0] % np.uint32(nc)) < rem: cnt += 1
        used = 0
        for _ in range(min(cnt, blk)):
            rest = 0
            for t in range(blk):
                if not ((used >> t) & 1): rest += on[c, bs + t]
            if rest == 0: break
            rng[0] = _xs32(rng[0]); r = np.int64(rng[0] % np.uint32(rest)); acc = 0
            for t in range(blk):
                if (used >> t) & 1: continue
                acc += on[c, bs + t]
                if r < acc:
                    used |= (1 << t); out[k] = bs + t; k += 1; break
    return k


def make_stage_xover(dreamfn='_dreamx'):
    base = re.sub(r"^@njit\(cache=True\)\n", "", inspect.getsource(cortex_slow._stage_slow.py_func))
    stage = base.replace("def _stage_slow(", "def _stage_xover(").replace("tick0):", "tick0, st, stc, blk, mixp):").replace("_dream(on, n, ", "_dreamx(on, n, st, stc, blk, mixp, ")
    ns = dict(cortex_slow.__dict__); ns.update(njit=njit, _dreamx=_dreamx, _dreamc=_dreamc, np=np); exec("@njit\n" + stage.replace("_dreamx(on, n, st, stc, blk, mixp, ", dreamfn + "(on, n, st, stc, blk, mixp, "), ns); return ns["_stage_xover"]


def make_stage_protect(shp):
    """protect-on-overlap (synaptic tagging): a real example's write on bit b is skipped with probability 1 - 2^-p where p = (sum over classes of |W[., b]|) >> shp, capped at 6: bits that the table already leans on heavily are hard to change, new knowledge goes mostly to quiet bits. shifts, adds, one xorshift draw."""
    src = f'''
@njit
def _practise_p(W, act, na, y, known, margin, cmax, rng):
    sc = _scores(W, act, na, known)
    t = sc[y]; rv = -1; best = -(1 << 30) - 1
    for c in range(W.shape[0]):
        if c != y and sc[c] > best:
            best = sc[c]; rv = c
    if rv < 0 or not known[rv] or t - best > margin:
        return 0
    for i in range(na):
        b = act[i]; imp = 0
        for c in range(W.shape[0]):
            imp += abs(W[c, b])
        p = min(6, imp >> {shp})
        if p > 0:
            rng[0] = _xs(rng[0])
            if (rng[0] >> 7) & ((1 << p) - 1) != 0:
                continue
        if W[y, b] < cmax:
            W[y, b] += 1
        if W[rv, b] > -cmax:
            W[rv, b] -= 1
    return 1
'''
    ns = dict(cortex_slow.__dict__); ns.update(njit=njit, _scores=_scores, np=np, _xs=_xs); exec(src, ns)
    base = re.sub(r"^@njit\(cache=True\)\n", "", inspect.getsource(cortex_slow._stage_slow.py_func))
    stage = base.replace("def _stage_slow(", "def _stage_protect(").replace("writes += _practise(W, acts[i], nacts[i], ys[i], known, margin, cmax)", "writes += _practise_p(W, acts[i], nacts[i], ys[i], known, margin, cmax, rng)")
    assert "_practise_p" in stage
    exec("@njit\n" + stage, ns); return ns["_stage_protect"]


@njit
def _practise_m(MK, W, act, na, y, known, margin, cmax):
    """context-gated practise: class c only owns the input bits of its context mask MK[c]; table entries outside the mask stay zero (so scoring ignores them) and are never written."""
    sc = _scores(W, act, na, known)
    t = sc[y]; rv = -1; best = -(1 << 30) - 1
    for c in range(W.shape[0]):
        if c != y and sc[c] > best:
            best = sc[c]; rv = c
    if rv < 0 or not known[rv] or t - best > margin:
        return 0
    for i in range(na):
        b = act[i]
        if MK[y, b] and W[y, b] < cmax:
            W[y, b] += 1
        if MK[rv, b] and W[rv, b] > -cmax:
            W[rv, b] -= 1
    return 1


def make_stage_gate():
    base = re.sub(r"^@njit\(cache=True\)\n", "", inspect.getsource(cortex_slow._stage_slow.py_func))
    stage = base.replace("def _stage_slow(", "def _stage_gate(").replace("tick0):", "tick0, MK):").replace("_practise(W, ", "_practise_m(MK, W, ")
    ns = dict(cortex_slow.__dict__); ns.update(njit=njit, _practise_m=_practise_m, np=np); exec("@njit\n" + stage, ns); return ns["_stage_gate"]


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


def n_cls_of(kw):
    return kw.get('n_cls', 10)


class CortexRules(CortexSlow):
    def __init__(self, n_bits, rule="split", par=0, **kw):
        super().__init__(n_bits, **kw); self.rule, self.par = rule, par; self._night = kw.get("night", 2)
        self._stage_g = make_stage_grade(par) if rule == "grade" else None
        if rule == "protect": self._sp = make_stage_protect(int(par or 3))
        if rule == "gate":
            self._sg = make_stage_gate(); g = np.random.RandomState(11); C = kw.get("n_cls", 10); self.ctxmask = np.zeros((C, n_bits), np.uint8); frac = (par or 50) / 100.0
            self._ctx = {}
            self._gen = lambda: (g.rand(n_bits) < frac).astype(np.uint8)
        if rule in ("xover", "catdream"):
            E = int(par or 8) if rule == "xover" else 1; self._sx = make_stage_xover("_dreamc" if rule == "catdream" else "_dreamx"); C = kw.get("n_cls", 10); self.xst = np.zeros((C, E, n_bits), np.uint8); self.xstc = np.zeros(C, np.int32); self.blk = int(os.environ.get("BLK", 32)); self.mixp = int(os.environ.get("REALMIX", 16))
        if rule == "real":
            E = int(par or 8); self.st = np.zeros((n_cls_of(kw), E, 1), np.int32); self.stn = np.zeros((n_cls_of(kw), E), np.int32); self.stc = np.zeros(n_cls_of(kw), np.int32)

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
        if self.rule == "protect":
            r = self._call(self._sp, code, y, self._night)
            if len(y) < 2 * self.ch: self.S[:] = self.W.astype(np.int32) << self.FR
            return r
        if self.rule == "gate":
            new = np.unique(y).astype(np.int64)
            if not any(self.known[c] for c in new): mk = self._gen()                              # a new context (stage): a fresh random mask over the input bits
            for c in new:
                if not self.known[c]: self.ctxmask[c] = mk
            old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]
            for c in new: self.known[c] = False if False else self.known[c]
            A, na = self.pack(code)
            r, self.tick = self._sg(self.W, self.S, self.on, self.n, self.rng, self.known, A, na, y.astype(np.int64), new, old.astype(np.int64), self.ndream, self._night, self.margin,
                                    self.cmax, self.top, self.daydream, self.night_stop, self.stats, self.ch, self.K, self.FR, self.RND, self.tick, self.ctxmask)
            if len(y) < 2 * self.ch: self.S[:] = self.W.astype(np.int32) << self.FR
            return r
        if self.rule in ("xover", "catdream"):
            for c in np.unique(y):
                if self.xstc[c] == 0:
                    for i in np.where(y == c)[0][:self.xst.shape[1]]: self.xst[c, self.xstc[c]] = code[i]; self.xstc[c] += 1
            new = np.unique(y).astype(np.int64); old = np.where(self.known & ~np.isin(np.arange(len(self.known)), new))[0]; A, na = self.pack(code)
            r, self.tick = self._sx(self.W, self.S, self.on, self.n, self.rng, self.known, A, na, y.astype(np.int64), new, old.astype(np.int64), self.ndream, self._night, self.margin,
                                    self.cmax, self.top, self.daydream, self.night_stop, self.stats, self.ch, self.K, self.FR, self.RND, self.tick, self.xst, self.xstc, self.blk, self.mixp)
            if len(y) < 2 * self.ch: self.S[:] = self.W.astype(np.int32) << self.FR
            return r
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
            if self.rule == "real":
                A, na = self.pack(code)
                if A.shape[1] > self.st.shape[2]:
                    ns = np.zeros(self.st.shape[:2] + (A.shape[1],), np.int32); ns[:, :, :self.st.shape[2]] = self.st; self.st = ns
                sc_all = code.astype(np.int32) @ self.W.T.astype(np.int32) if os.environ.get("HARD") else None
                for c in np.unique(y):
                    if self.stc[c] == 0:
                        ids = np.where(y == c)[0]
                        if sc_all is not None:                               # keep the hardest examples: smallest gap between the right class and the best rival (the ones the day had to correct)
                            s_ = sc_all[ids].copy(); t_ = s_[:, c].copy(); s_[:, c] = -(1 << 30); s_[:, ~self.known] = -(1 << 30); gap_ = t_ - s_.max(1); ids = ids[np.argsort(np.where(gap_ < 0, 1 << 20, gap_))] if os.environ.get('HARD') == '2' else ids[np.argsort(gap_)]     # HARD=2: hardest among the correctly classified (misclassified outliers last)
                        for i in ids[:self.st.shape[1]]:
                            q = self.stc[c]; self.st[c, q, :A.shape[1]] = A[i]; self.stn[c, q] = na[i]; self.stc[c] += 1
            if len(np.where(self.known)[0]) > len(np.unique(y)):
                if self.rule == "real":
                    kn = np.where(self.known)[0]; total = self.ndream * len(kn) * self._night
                    mixc = np.full(len(self.known), int(os.environ.get("REALMIX", 8)), np.int64)
                    if os.environ.get("ADAPT"):                              # self-test: the fraction of a class's stored hard traces the table now gets wrong sets that class's real-replay share (0 when all are still recognised)
                        Wi = self.W.astype(np.int32); mixc[:] = 0
                        for c in kn:
                            if self.stc[c] == 0: continue
                            bad = 0
                            for q in range(self.stc[c]):
                                sc_ = Wi[:, self.st[c, q, :self.stn[c, q]]].sum(1); sc_[~self.known] = -(1 << 30); bad += int(sc_.argmax() != c)
                            mixc[c] = (16 * bad) // self.stc[c]
                    self.tick = _night_real(self.W, self.S, self.on, self.n, self.rng, self.known, self.st, self.stn, self.stc, int(total), mixc, int(os.environ.get("DROP", 0)), int(os.environ.get("RMARGIN", self.margin)), self.margin, self.cmax, self.top, self.ch, self.K, self.FR, self.RND, self.tick, self.night_stop, self.stats)
                elif self.rule == "prio":
                    kn = np.where(self.known)[0]; total = self.ndream * len(kn) * self._night
                    self.tick = _night_prio(self.W, self.S, self.on, self.n, self.rng, self.known, int(total), self.margin, self.cmax, self.top, self.ch, self.K, self.FR, self.RND, self.tick, int(self.par or 256))
                else: self._night_only()
        if len(y) < 2 * self.ch: self.S[:] = self.W.astype(np.int32) << self.FR
        return r
