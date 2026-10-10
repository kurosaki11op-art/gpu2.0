"""Multi-scale recall memory (hardware-exact model) used for memory-aware training and evaluation.

One table of len(orders) x 2^bits slots. Slot = {order index, h1(context)}, tag = h2(context) (tag_bits),
value = next byte, conf = 2-bit saturating counter. Each order that recognises the current context adds
BOOST[order][conf] to its remembered byte's logit ("memory priming")."""
import numpy as np

M32 = 0xFFFFFFFF
ORDERS = (2, 3, 4, 6)
BOOST = np.array([[((64 + 32 * c) * k) // 3 for c in range(4)] for k in ORDERS], np.int64)


def fold(ctx):
    return (ctx ^ (ctx >> 32)) & M32


def h1(x, bits):
    return ((x * 0x9E3779B1) & M32) >> (32 - bits)


def h2(x, tb):
    return ((x * 0x85EBCA6B) & M32) >> (32 - tb)


def hits(seq, orders=ORDERS, bits=10, tb=8):
    """For each position t: (value, conf) per order for predicting seq[t+1]; -1 = no hit."""
    seq = [int(b) for b in seq]
    n = len(seq); T = {}; hist = 0; masks = [(1 << (8 * k)) - 1 for k in orders]
    H = np.full((n, len(orders), 2), -1, np.int16)
    for t in range(n):
        b = seq[t]
        if t > 0:
            for oi, k in enumerate(orders):
                if t < k:
                    continue
                x = fold(hist & masks[oi]); s = (oi << bits) | h1(x, bits); tg = h2(x, tb); e = T.get(s)
                if e is not None and e[0] == tg:
                    if e[1] == b:
                        e[2] = min(e[2] + 1, 3)
                    else:
                        e[1] = b; e[2] = 0
                else:
                    T[s] = [tg, b, 0]
        hist = ((hist << 8) | b) & 0xFFFFFFFFFFFF
        for oi, k in enumerate(orders):
            if t + 1 < k:
                continue
            x = fold(hist & masks[oi]); s = (oi << bits) | h1(x, bits); tg = h2(x, tb); e = T.get(s)
            if e is not None and e[0] == tg:
                H[t, oi, 0] = e[1]; H[t, oi, 1] = e[2]
    return H


def boost_logits(LM, H, B=BOOST):
    lg = LM.astype(np.int64).copy(); rows = np.arange(len(H))
    for oi in range(H.shape[1]):
        v, c = H[:, oi, 0].astype(np.int64), H[:, oi, 1].astype(np.int64); m = v >= 0
        np.add.at(lg, (rows[m], v[m]), B[oi][c[m]])
    return lg
