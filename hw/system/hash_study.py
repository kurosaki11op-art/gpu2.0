"""Which multiplier-free hash keeps the lookup design as accurate as the multiplicative hash?
Hashes: mult (the golden model's constant multiply), xor (xor-fold + xorshift), tab (tabulation hashing: XOR of one ROM word per
context byte, no arithmetic at all), crc (CRC-32, an LFSR: XOR and shifts). Lookup design: orders 2,3,4,6, 2^12 entries per table, hysteresis counters.
Reports accuracy and table coverage on 20,000 bytes of code and the four prose slices.
usage: python hash_study.py <book dir>"""
import json, os, sys, zlib
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "golden"))
import spark_golden_v2 as g2  # noqa
M32 = 0xFFFFFFFF
rng = np.random.default_rng(7); TAB = [[int(x) for x in rng.integers(0, 2 ** 32, 256, dtype=np.uint64)] for _ in range(6)]


def h_mult(x, salt, order): return g2.h32(x, salt)
def h_xor(x, salt, order):
    x = (x ^ (x >> 16) ^ (x >> 32) ^ (salt * 0x01010101 & M32)) & M32
    x ^= (x << 13) & M32; x ^= x >> 17; x ^= (x << 5) & M32
    return x
def h_tab(x, salt, order):
    v = (salt * 0x01010101) & M32
    for j in range(order): v ^= TAB[j][(x >> (8 * j)) & 255]
    return v
def h_crc(x, salt, order): return zlib.crc32(x.to_bytes(6, "little"), salt) & M32


def lookup(text, hash_fn, orders=(2, 3, 4, 6), tb=12):
    N = len(text); tables = [dict() for _ in orders]; hist = 0; pred = np.zeros(N, int); hit = np.zeros(N, bool)

    def slot(k, h):
        v = hash_fn(h & ((1 << (8 * orders[k])) - 1), k + 1, orders[k]); return v >> (32 - tb), (v >> 4) & 0xFFF
    for i in range(N):
        hist = ((hist << 8) | int(text[i])) & ((1 << 48) - 1); pred[i] = 32
        for k in reversed(range(len(orders))):
            s, t = slot(k, hist); e = tables[k].get(s)
            if e and e[0] == t: pred[i] = e[1]; hit[i] = True; break
        if i + 1 < N:
            nxt = int(text[i + 1])
            for k in range(len(orders)):
                s, t = slot(k, hist); e = tables[k].get(s)
                if e and e[0] == t:
                    if e[1] == nxt: e[2] = min(e[2] + 1, 3)
                    elif e[2] > 0: e[2] -= 1
                    else: e[1] = nxt
                else: tables[k][s] = [t, nxt, 0]
    return pred, hit


if __name__ == "__main__":
    Z = np.load(os.path.join(HERE, "out", "slice_cache.npz")); code = Z["test_text"]
    slices = {"code": code}
    for b in ("carroll-alice.txt", "melville-moby_dick.txt", "shakespeare-hamlet.txt", "austen-emma.txt"):
        raw = np.frombuffer(open(os.path.join(sys.argv[1], b), "rb").read(), dtype=np.uint8); s0 = int(len(raw) * 0.4)
        slices[b.split(".")[0]] = raw[s0:s0 + 20000]
    out = {}
    for hn, fn in (("mult", h_mult), ("xor", h_xor), ("tab", h_tab), ("crc", h_crc)):
        row = {}
        for sn, t in slices.items():
            p, h = lookup(t, fn); row[sn] = {"acc": float((p[:-1] == t[1:]).mean()), "coverage": float(h.mean())}
        row["prose_mean"] = float(np.mean([row[k]["acc"] for k in row if k != "code"]))
        out[hn] = row; print(hn, "code", round(row["code"]["acc"], 4), "prose mean", round(row["prose_mean"], 4),
                             "coverage code/prose", round(row["code"]["coverage"], 3), round(np.mean([row[k]["coverage"] for k in row if k not in ("code", "prose_mean")]), 3), flush=True)
    json.dump(out, open(os.path.join(HERE, "..", "results", "hash_study.json"), "w"), indent=1)
