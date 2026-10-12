"""Matrix-free lookup predictor, literally multiplier-free: the hash uses only XOR, shifts and folds (no constant multiply).
Sweeps table size and order set; reports accuracy vs the true next byte, agreement with the GPU stand-in model, and table memory.
Entry = 12-bit tag + 8-bit value + 2-bit count = 22 bits. Online one-pass learning with the hysteresis counter rule."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
text, big = Z["test_text"], Z["test_big_pred"]; N = len(text); M32 = 0xFFFFFFFF


def xhash(x, salt):
    x = (x ^ (x >> 16) ^ (x >> 32) ^ (salt * 0x01010101 & M32)) & M32      # fold 48 bits to 32 (xor + shifts only)
    x ^= (x << 13) & M32; x ^= x >> 17; x ^= (x << 5) & M32                 # xorshift32
    return x


def run(orders, tb, hash_fn=xhash):
    tables = [dict() for _ in orders]; hist = 0; pred = np.zeros(N, int)

    def slot(k, h):
        v = hash_fn(h & ((1 << (8 * orders[k])) - 1), k + 1); return v >> (32 - tb), (v >> 4) & 0xFFF
    for i in range(N):
        hist = ((hist << 8) | int(text[i])) & ((1 << 48) - 1); pred[i] = 32
        for k in reversed(range(len(orders))):
            s, t = slot(k, hist); e = tables[k].get(s)
            if e and e[0] == t:
                pred[i] = e[1]; break
        if i + 1 < N:
            nxt = int(text[i + 1])
            for k in range(len(orders)):
                s, t = slot(k, hist); e = tables[k].get(s)
                if e and e[0] == t:
                    if e[1] == nxt: e[2] = min(e[2] + 1, 3)
                    elif e[2] > 0: e[2] -= 1
                    else: e[1] = nxt
                else: tables[k][s] = [t, nxt, 0]
    return float((pred[:-1] == text[1:]).mean()), float((pred[:-1] == big[:-1]).mean())


rows = []
for orders in ((1, 2, 3, 4, 6), (2, 3, 4, 6), (1, 2, 4), (2, 4)):
    for tb in (9, 10, 11, 12):
        acc, agr = run(orders, tb); kb = len(orders) * (1 << tb) * 22 / 8 / 1024
        rows.append({"orders": orders, "table_bits": tb, "memory_KB": kb, "acc_true": acc, "agree_gpu": agr})
        print(f"orders {str(orders):14s} 2^{tb:<2d} entries/table  {kb:6.1f} KB  acc {acc:.1%}  agree-GPU {agr:.1%}", flush=True)
json.dump(rows, open(os.path.join(HERE, "..", "results", "matrix_free_sweep.json"), "w"), indent=1)
