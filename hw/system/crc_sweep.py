"""Size sweep of the matrix-free lookup design with a CRC-32 (XOR/shift only) hash: orders x entries per table, on code and prose.
usage: python crc_sweep.py <book dir>"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import hash_study as hs  # noqa
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz")); slices = {"code": Z["test_text"]}
for b in ("carroll-alice.txt", "melville-moby_dick.txt", "shakespeare-hamlet.txt", "austen-emma.txt"):
    raw = np.frombuffer(open(os.path.join(sys.argv[1], b), "rb").read(), dtype=np.uint8); s0 = int(len(raw) * 0.4)
    slices[b.split(".")[0]] = raw[s0:s0 + 20000]
rows = []
for orders in ((2, 4), (2, 3, 4, 6), (1, 2, 3, 4, 6)):
    for tb in (10, 11, 12):
        acc = {k: float((hs.lookup(t, hs.h_crc, orders, tb)[0][:-1] == t[1:]).mean()) for k, t in slices.items()}
        kb = len(orders) * (1 << tb) * 22 / 8 / 1024
        r = {"orders": orders, "entries_log2": tb, "memory_KB": kb, "code": acc["code"], "prose_mean": float(np.mean([v for k, v in acc.items() if k != "code"]))}
        rows.append(r); print(f"orders {str(orders):14s} 2^{tb} {kb:6.1f} KB  code {r['code']:.1%}  prose {r['prose_mean']:.1%}", flush=True)
json.dump(rows, open(os.path.join(HERE, "..", "results", "crc_sweep.json"), "w"), indent=1)
