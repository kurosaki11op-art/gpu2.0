"""Bit-exact reference model of the SPARK-L lookup core (hw/rtl/lookup/spark_lookup.v).
Orders 2,3,4,6; CRC-32 hash (zlib), slot = top TB bits, tag = bits 15..4; entries {valid, tag, value, count}; hysteresis learning."""
import zlib

ORDERS = (2, 3, 4, 6)


def slot_tag(hist, k, tb):
    x = hist & ((1 << (8 * ORDERS[k])) - 1)
    v = zlib.crc32(x.to_bytes(6, "little"), k + 1) & 0xFFFFFFFF
    return v >> (32 - tb), (v >> 4) & 0xFFF


class LookupCore:
    def __init__(self, tb=12):
        self.tb = tb; self.t = [dict() for _ in ORDERS]; self.hist = 0; self.prev = None

    def step(self, b):
        if self.prev is not None:                       # learn the byte that followed each stored context
            for k, (s, tag) in enumerate(self.prev):
                e = self.t[k].get(s)
                if e and e[0] == tag:
                    if e[1] == b: e[2] = min(e[2] + 1, 3)
                    elif e[2] > 0: e[2] -= 1
                    else: e[1] = b
                else: self.t[k][s] = [tag, b, 0]
        self.hist = ((self.hist << 8) | b) & ((1 << 48) - 1)
        self.prev = [slot_tag(self.hist, k, self.tb) for k in range(len(ORDERS))]
        for k in reversed(range(len(ORDERS))):
            s, tag = self.prev[k]; e = self.t[k].get(s)
            if e and e[0] == tag: return e[1], 1, k, e[2]
        return 0x20, 0, 0, 0


if __name__ == "__main__":
    print("CRC", *("%08x" % (zlib.crc32(int(x, 16).to_bytes(6, "little"), s) & 0xFFFFFFFF)
                   for x, s in (("00000000_6261".replace("_", ""), 1), ("0123456789AB", 4), ("FFFFFFFFFFFF", 3))))


class LookupCoreV2:
    """Bit-exact reference for spark_lookup2.v: 2-way set-associative hashed tables (orders 2,3,4,6; 2^TB sets;
    slot = {lru, way1, way0}, entry = {valid, tag[11:0], value[7:0], count[1:0]}), a direct-mapped order-1 table
    (256 entries, {valid, value, count}) as fallback, and a confidence bucket for a 32-entry lookup table.
    LRU rule: a learning hit on way w makes the other way least-recently-used; a miss installs into an invalid way if any
    (way 0 first), else into the LRU way, and the other way becomes LRU. Prediction does not change LRU.
    Returns (pred, hit, src, count, bucket): src 0-3 = hashed order 2/3/4/6, 4 = order-1 table, 5 = none;
    bucket = src*4 + count for src < 5, 20 for none."""

    def __init__(self, tb=11):
        self.tb = tb; self.t = [dict() for _ in ORDERS]; self.o1 = {}; self.hist = 0; self.prev = None

    @staticmethod
    def _learn(e, b):                                   # e = [value, count], tag already matched
        if e[0] == b: e[1] = min(e[1] + 1, 3)
        elif e[1] > 0: e[1] -= 1
        else: e[0] = b

    def step(self, b):
        if self.prev is not None:
            for k, (s, tag) in enumerate(self.prev):
                ways, lru = self.t[k].get(s, ([None, None], 0))
                ways = list(ways)
                w = next((i for i in (0, 1) if ways[i] is not None and ways[i][0] == tag), None)
                if w is not None:
                    e = [ways[w][1], ways[w][2]]; self._learn(e, b); ways[w] = (tag, e[0], e[1]); lru = 1 - w
                else:
                    v = 0 if ways[0] is None else (1 if ways[1] is None else lru)
                    ways[v] = (tag, b, 0); lru = 1 - v
                self.t[k][s] = (ways, lru)
            last = self.hist & 255; e = self.o1.get(last)
            if e is None: self.o1[last] = [b, 0]
            else: self._learn(e, b)
        self.hist = ((self.hist << 8) | b) & ((1 << 48) - 1)
        self.prev = [slot_tag(self.hist, k, self.tb) for k in range(len(ORDERS))]
        for k in reversed(range(len(ORDERS))):
            s, tag = self.prev[k]; ways, _ = self.t[k].get(s, ([None, None], 0))
            for e in ways:
                if e is not None and e[0] == tag: return e[1], 1, k, e[2], k * 4 + e[2]
        e = self.o1.get(b)
        if e is not None: return e[0], 1, 4, e[1], 16 + e[1]
        return 0x20, 0, 5, 0, 20
