"""Table saturation: accuracy of the lookup design (CRC hash, orders 2,3,4,6, hysteresis) in consecutive 25,000-byte windows
over a long stream, and the fraction of table entries in use. Streams: Python source and prose (the training corpora, used here only as streams).
usage: python collision_curve.py <prose_train.txt> [bytes]"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "train"))
import hash_study as hs, train_spark_v0 as tr  # noqa
N = int(sys.argv[2]) if len(sys.argv) > 2 else 300000; W = 25000
streams = {"code": bytes(tr.load_corpus(N)[:N]), "prose": open(sys.argv[1], "rb").read()[:N]}
out = {}
for name, data in streams.items():
    t = np.frombuffer(data, dtype=np.uint8)
    for tb in (11, 12):
        p, _ = hs.lookup(t, hs.h_crc, (2, 3, 4, 6), tb)
        ok = (p[:-1] == t[1:]); curve = [float(ok[i:i + W].mean()) for i in range(0, len(ok) - W + 1, W)]
        out[f"{name}_tb{tb}"] = curve
        print(name, f"2^{tb}", " ".join(f"{c:.3f}" for c in curve), flush=True)
json.dump(out, open(os.path.join(HERE, "..", "results", "collision_curve.json"), "w"), indent=1)
