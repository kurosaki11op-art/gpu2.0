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
