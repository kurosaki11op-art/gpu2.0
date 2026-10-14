"""Can the lookup-only design close its gap to the network hybrid without a network?
Variants (CRC-32 hash, hysteresis counters, no multipliers) vs the hybrid's cached predictions on the same 5 documents (paired, block bootstrap).
Ideas: (a) direct-mapped order-1 table as the fallback (256 entries, no hash); (b) order-0 fallback = most frequent byte so far;
(c) longer contexts (orders 8, 12) for copy-like repeats; (d) 2-way set-associative tables (same memory as 1-way at twice the entries).
usage: python close_gap.py <book dir>"""
import json, os, sys, zlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
M32 = 0xFFFFFFFF


class Lookup:
    def __init__(self, orders=(2, 3, 4, 6), tb=12, ways=1, o1=False, o0=False):
        self.orders, self.tb, self.ways, self.o1, self.o0 = orders, tb, ways, o1, o0
        self.t = [dict() for _ in orders]; self.d1 = {}; self.freq = np.zeros(256, int); self.best = 32
        self.hist = 0; self.prev = None

    def key(self, k):
        o = self.orders[k]; x = self.hist & ((1 << (8 * o)) - 1)
        v = zlib.crc32(x.to_bytes(16, "little"), k + 1) & M32
        return v >> (32 - self.tb), (v >> 4) & 0xFFF

    @staticmethod
    def learn(e, b):
        if e[1] == b: e[2] = min(e[2] + 1, 3)
        elif e[2] > 0: e[2] -= 1
        else: e[1] = b

    def step(self, b):
        if self.prev is not None:
            for k, (s, tag) in enumerate(self.prev):
                if k == len(self.orders): continue
                way = self.t[k].setdefault(s, [])
                e = next((x for x in way if x[0] == tag), None)
                if e: self.learn(e, b); way.remove(e); way.insert(0, e)          # keep most recently used first
                else:
                    if len(way) >= self.ways: way.pop()                        # evict the least recently used
                    way.insert(0, [tag, b, 0])
            if self.o1:
                last = self.hist & 255; e = self.d1.get(last)
                if e: self.learn([0] + e[:], b) or None
                if e:
                    x = [0, e[0], e[1]]; self.learn(x, b); self.d1[last] = [x[1], x[2]]
                else: self.d1[last] = [b, 0]
            if self.o0:
                self.freq[b] += 1
                if self.freq[b] > self.freq[self.best]: self.best = b
        self.hist = ((self.hist << 8) | b) & ((1 << 128) - 1)
        self.prev = [self.key(k) for k in range(len(self.orders))]
        for k in reversed(range(len(self.orders))):
            s, tag = self.prev[k]
            e = next((x for x in self.t[k].get(s, []) if x[0] == tag), None)
            if e: return e[1]
        if self.o1 and (b in self.d1): return self.d1[b][0]
        if self.o0: return self.best
        return 32

    def memory_kb(self):
        kb = len(self.orders) * (1 << self.tb) * self.ways * (23 + (1 if self.ways > 1 else 0)) / 8 / 1024
        return kb + (256 * 11 / 8 / 1024 if self.o1 else 0) + (256 * 16 / 8 / 1024 if self.o0 else 0)


def docs(book_dir):
    import nontext_probe as npb
    Z = np.load(os.path.join(HERE, "out", "slice_cache.npz")); d = {"code": bytes(Z["test_text"])}
    for b in npb.BOOKS:
        raw = open(os.path.join(book_dir, b), "rb").read(); s0 = int(len(raw) * 0.4); d[b.split(".")[0]] = raw[s0:s0 + 20000]
    return d


def hybrid_cache(D):
    fn = os.path.join(HERE, "out", "hybrid_preds.npz")
    if os.path.exists(fn): return dict(np.load(fn))
    import paired_stats as ps  # noqa  (runs its own analysis at import; avoid) -- not used
    raise SystemExit("run make_hybrid_cache first")


rng = np.random.default_rng(0)


def boot(d, block=250, reps=2000):
    nb = len(d) // block; m = d[:nb * block].reshape(nb, block).mean(1)
    s = [m[rng.integers(0, nb, nb)].mean() for _ in range(reps)]
    return np.percentile(s, 2.5), np.percentile(s, 97.5)


if __name__ == "__main__":
    D = docs(sys.argv[1]); H = dict(np.load(os.path.join(HERE, "out", "hybrid_preds.npz")))
    variants = {
        "baseline 2,3,4,6": dict(),
        "+ order-1 direct": dict(o1=True),
        "+ order-1 + order-0": dict(o1=True, o0=True),
        "+ o1 + o0, orders 2,3,4,6,8": dict(orders=(2, 3, 4, 6, 8), o1=True, o0=True),
        "+ o1 + o0, orders 2,3,4,6,8,12": dict(orders=(2, 3, 4, 6, 8, 12), o1=True, o0=True),
        "+ o1 + o0, 2-way, 2^11 x2": dict(tb=11, ways=2, o1=True, o0=True),
        "+ o1 + o0, 2-way, orders 2,3,4,6,8, 2^11 x2": dict(orders=(2, 3, 4, 6, 8), tb=11, ways=2, o1=True, o0=True),
    }
    res = {}
    for name, kw in variants.items():
        okv = {}; per = {}
        for dn, text in D.items():
            L = Lookup(**kw); p = np.array([L.step(b) for b in text])[:-1]; tt = np.frombuffer(text, dtype=np.uint8)[1:]
            okv[dn] = (p == tt); per[dn] = float(okv[dn].mean())
        row = {"memory_KB": Lookup(**kw).memory_kb(), "per_doc": per}
        for mode in (0, 2):
            d = np.concatenate([okv[dn].astype(float) - (H[f"{dn}_m{mode}"][:-1] == np.frombuffer(D[dn], dtype=np.uint8)[1:]).astype(float) for dn in D])
            lo, hi = boot(d); row[f"vs_hybrid_mode{mode}"] = [float(d.mean()), float(lo), float(hi)]
        res[name] = row
        print(f"{name:45s} {row['memory_KB']:6.1f} KB  code {per['code']:.1%}  prose {np.mean([v for k, v in per.items() if k != 'code']):.1%}  "
              f"vs hybrid(miss-only) {row['vs_hybrid_mode0'][0]*100:+.2f} [{row['vs_hybrid_mode0'][1]*100:+.2f},{row['vs_hybrid_mode0'][2]*100:+.2f}]  "
              f"vs hybrid(arbitrating) {row['vs_hybrid_mode2'][0]*100:+.2f} [{row['vs_hybrid_mode2'][1]*100:+.2f},{row['vs_hybrid_mode2'][2]*100:+.2f}]", flush=True)
    json.dump(res, open(os.path.join(HERE, "..", "results", "close_gap.json"), "w"), indent=1)
