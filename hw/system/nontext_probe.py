"""Non-code text test: does the network earn its place on prose? Compares, on 20,000-byte slices of public-domain books
(NLTK Gutenberg set; slice taken at 40% of each book):
  * matrix-free lookup (XOR/shift hash, orders 1,2,3,4,6, hysteresis counters; 2^12 and 2^11 entries per table)
  * SPARK v2 full: network trained on CODE (out_qat_sp0.05) + recall memory (replace rule), as in earlier tests
  * SPARK v2 full with the hysteresis recall update
  * a trivial baseline (always predict a space)
All start with empty memories at the slice start. Metric: accuracy vs the true next byte.
usage: python nontext_probe.py <dir with the .txt books>"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (os.path.join(HERE, "..", "golden"), HERE):
    sys.path.insert(0, p)
import spark_golden as g1, spark_golden_v2 as g2  # noqa
import recall_policy as rp  # noqa
M32 = 0xFFFFFFFF
BOOKS = ("carroll-alice.txt", "melville-moby_dick.txt", "shakespeare-hamlet.txt", "austen-emma.txt")
lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
CFG = dict(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16)


def xhash(x, salt):
    x = (x ^ (x >> 16) ^ (x >> 32) ^ (salt * 0x01010101 & M32)) & M32
    x ^= (x << 13) & M32; x ^= x >> 17; x ^= (x << 5) & M32
    return x


def lookup(text, orders=(1, 2, 3, 4, 6), tb=12):
    N = len(text); tables = [dict() for _ in orders]; hist = 0; pred = np.zeros(N, int)

    def slot(k, h):
        v = xhash(h & ((1 << (8 * orders[k])) - 1), k + 1); return v >> (32 - tb), (v >> 4) & 0xFFF
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
    return pred


def spark(text, hyst):
    cfg = g1.Cfg(**CFG)
    g = rp.Policy(W, cfg, tb=12, lut=lut, update="hyst") if hyst else g2.GoldenV2(W, cfg, tb=12, lut=lut)
    return np.array([g.step(int(b))["pred"] for b in text])


res = {}
for name in BOOKS:
    raw = np.frombuffer(open(os.path.join(sys.argv[1], name), "rb").read(), dtype=np.uint8)
    s0 = int(len(raw) * 0.4); text = raw[s0:s0 + 20000]; tt = text[1:]
    row = {"always_space": float((tt == 32).mean())}
    for label, p in (("lookup_55KB", lookup(text, tb=12)), ("lookup_27KB", lookup(text, tb=11)),
                     ("spark_full", spark(text, False)), ("spark_full_hyst", spark(text, True))):
        row[label] = float((p[:-1] == tt).mean())
    res[name] = row; print(name, json.dumps({k: round(v, 3) for k, v in row.items()}), flush=True)
avg = {k: float(np.mean([r[k] for r in res.values()])) for k in next(iter(res.values()))}
print("mean", json.dumps({k: round(v, 3) for k, v in avg.items()}))
json.dump({"per_book": res, "mean": avg}, open(os.path.join(HERE, "..", "results", "nontext_probe.json"), "w"), indent=1)
