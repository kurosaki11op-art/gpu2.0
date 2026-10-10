"""SPARK v2 golden model (extends the bit-exact v1 model in spark_golden.py).

v2 additions (all integer, RTL-implementable):
  * Multi-order recall memory: one table per context order in ORDERS, 2**tb entries each,
    entry = {12-bit tag, 8-bit value, 2-bit count}. Back-off: the highest order with a confident hit answers.
  * Confidence output conf8 (0..255) read from a programmable 128-entry LUT indexed by a feature bucket:
      recall answer (skip network)     : order_idx*12 + count*3 + agree (0..47)
                                         agree: 0 a lower-order table disagrees, 1 no other hit, 2 one agrees
      early-exit head                  : 48 + log2-bucket(exit margin)  (48..63)
      main head                        : 64 + log2-bucket(main margin)  (64..79)
      recall vs main arbitration       : 80 + log2-bucket(main margin)  (80..95)
    The LUT is trained offline with RLCD-style calibration and can be rewritten over the host interface.
  * Online calibration (on-chip learning): per-bucket counters (seen, agreed), updated when the host feeds
    back the GPU's answer; the LUT entry becomes 255*agreed/seen (counters halve at 255: forgetting).
The spiking network (stages, spikes, early exit) is the unchanged v1 datapath.
"""
import numpy as np
import spark_golden as g1

ORDERS = (2, 3, 4, 6)
NB = 128           # LUT entries (7-bit bucket index)


def mbucket(m):
    m = int(m)
    return 0 if m <= 0 else min(15, m.bit_length())


def h32(x, salt):
    x = (x ^ (salt * 0x5BD1E995)) & 0xFFFFFFFFFFFF
    x ^= x >> 29
    return ((x * 0x9E3779B1) ^ (x >> 16)) & 0xFFFFFFFF


class GoldenV2(g1.Golden):
    def __init__(self, wts, cfg, tb=11, orders=ORDERS, lut=None):
        super().__init__(wts, cfg)
        self.tb, self.orders = tb, orders
        self.tables = [dict() for _ in orders]
        self.hist6 = 0
        self.lut = np.array(lut if lut is not None else [128] * NB, dtype=np.int64)
        self.seen = np.zeros(NB, np.int64)
        self.agree = np.zeros(NB, np.int64)
        self.last = None

    def _slot(self, k, hist):
        h = h32(hist & ((1 << (8 * self.orders[k])) - 1), k + 1)
        return h >> (32 - self.tb), (h >> 4) & 0xFFF

    def feedback(self, gpu_byte):
        if self.last is None:
            return
        b, p = self.last
        self.seen[b] += 1
        self.agree[b] += int(p == gpu_byte)
        if self.seen[b] >= 8:
            self.lut[b] = (255 * self.agree[b]) // self.seen[b]
        if self.seen[b] >= 255:
            self.seen[b] >>= 1
            self.agree[b] >>= 1

    def step(self, b):
        c = self.c
        prev = self.hist6
        self.hist6 = ((prev << 8) | b) & ((1 << 48) - 1)
        best = None
        if c.recall:
            for k in range(len(self.orders)):
                i, tag = self._slot(k, prev)
                e = self.tables[k].get(i)
                if e and e[0] == tag:
                    e = [tag, b, min(e[2] + 1, 3)] if e[1] == b else [tag, b, 0]
                else:
                    e = [tag, b, 0]
                self.tables[k][i] = e
            hits = []
            for k in reversed(range(len(self.orders))):
                i, tag = self._slot(k, self.hist6)
                e = self.tables[k].get(i)
                if e and e[0] == tag and e[2] >= c.conf_th:
                    hits.append((k, e[1], e[2]))
            if hits:
                k, v, cnt = hits[0]
                others = [h[1] for h in hits[1:]]
                agree = 1 if not others else (2 if v in others else 0)   # 0 lower order disagrees, 1 alone, 2 agrees
                best = (k, v, cnt, agree)
        out = {"ev": [0, 0, 0, 0], "proc": [0, 0, 0, 0], "mexit": -1, "mmain": -1, "rbest": best}
        x_in = self._input(b)
        self.tok += 1
        if best is not None and c.recall_mode == 0:
            out.update(pred=best[1], path=2, bucket=best[0] * 12 + best[2] * 3 + best[3])
        else:
            def stage(k, src):
                out["ev"][k], out["proc"][k] = self._events(k, src)
            stage(0, x_in)
            self._membrane(0, 0)
            done = False
            if best is None and c.exit_en and ((not c.adapt) or self.score >= 4 or (self.tok & 15) == 1):
                stage(2, self.s[0])
                idx, m = self._argmax(2)
                out["mexit"] = m
                if m >= c.exit_th:
                    self.score = min(self.score + 2, 15)
                    out.update(pred=idx, path=1, bucket=48 + mbucket(m))
                    done = True
                else:
                    self.score = max(self.score - 1, 0)
            if not done:
                stage(1, self.s[0])
                self._membrane(1, 1)
                stage(3, self.s[1])
                idx, m = self._argmax(3)
                out["mmain"] = m
                out["main_pred"] = idx
                if best is not None and m < c.arb_th:
                    out.update(pred=best[1], path=2, bucket=80 + mbucket(m))
                else:
                    out.update(pred=idx, path=0, bucket=64 + mbucket(m))
        out["conf"] = int(self.lut[out["bucket"]])
        self.last = (out["bucket"], out["pred"])
        return out


class GoldenV2Multi:
    """NS independent streams (users). Network state, context and feedback slot are per stream;
    the recall memory, confidence LUT and calibration counters are shared (patterns learned from every user)."""
    def __init__(self, wts, cfg, ns=2, **kw):
        self.s = [GoldenV2(wts, cfg, **kw) for _ in range(ns)]
        for x in self.s[1:]:
            x.tables, x.lut, x.seen, x.agree = self.s[0].tables, self.s[0].lut, self.s[0].seen, self.s[0].agree

    def step(self, sid, b):
        return self.s[sid].step(b)

    def feedback(self, sid, gpu_byte):
        self.s[sid].feedback(gpu_byte)
