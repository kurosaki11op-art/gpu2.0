"""Bit-exact reference for spark_lookup_tok.v: token-level lookup drafter (the design measured by token_lookup_test.py).
Orders 1-4 (tokens), one hashed table per order (2^TB entries, 1-way), entry = {valid, tag[11:0], value[TW-1:0], count[1:0]}.
Hash: zlib.crc32 over the last o token IDs, each as 4 little-endian bytes, oldest first, start value = order index + 1.
learn(tok): update every order whose context exists, then append tok. draft(K): chain lookups from the committed history,
highest order first, stop at the first miss; returns [(token, order_idx, count)]; drafting never writes the tables."""
import zlib


class TokCore:
    def __init__(self, tb=12):
        self.tb = tb; self.t = [dict() for _ in range(4)]; self.hist = []

    def key(self, h, k):
        o = k + 1; v = zlib.crc32(b"".join(int(x).to_bytes(4, "little") for x in h[-o:]), k + 1) & 0xFFFFFFFF
        return v >> (32 - self.tb), (v >> 4) & 0xFFF

    def learn(self, tok):
        for k in range(4):
            if len(self.hist) < k + 1: continue
            s, tag = self.key(self.hist, k); e = self.t[k].get(s)
            if e and e[0] == tag:
                if e[1] == tok: e[2] = min(e[2] + 1, 3)
                elif e[2] > 0: e[2] -= 1
                else: e[1] = tok
            else: self.t[k][s] = [tag, tok, 0]
        self.hist = (self.hist + [tok])[-4:]

    def draft(self, K):
        h = list(self.hist); out = []
        while len(out) < K:
            got = None
            for k in reversed(range(4)):
                if len(h) < k + 1: continue
                s, tag = self.key(h, k); e = self.t[k].get(s)
                if e and e[0] == tag: got = (e[1], k, e[2]); break
            if got is None: break
            out.append(got); h = (h + [got[0]])[-4:]
        return out
