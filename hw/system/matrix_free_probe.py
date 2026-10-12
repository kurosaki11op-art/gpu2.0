"""Can a predictor with NO matrices and NO multiplications do the job? A pure lookup model: multi-order hashed tables
(entry = tag, value, 2-bit count), hysteresis update (a local, one-pass, gradient-free learning rule), highest-order hit answers,
fallback = most recent successor of the last byte (order 1), else a space. Only hashing, compares, counters and table reads/writes.
Compared on the held-out test slice with the full SPARK v2 (network + recall), using the cached predictions.
Metrics: accuracy vs the true next byte, agreement with the GPU stand-in model's greedy byte, coverage (bytes answered by a table hit),
and a learning curve (accuracy vs bytes seen)."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "golden"))
import spark_golden_v2 as g2  # noqa
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz"))
text, big, sp = Z["test_text"], Z["test_big_pred"], Z["test_sp"]
N = len(text); ORDERS = (1, 2, 3, 4, 6); TB = 12


def slot(k, hist):
    h = g2.h32(hist & ((1 << (8 * ORDERS[k])) - 1), k + 1)
    return h >> (32 - TB), (h >> 4) & 0xFFF


tables = [dict() for _ in ORDERS]; hist = 0; pred = np.zeros(N, int); hit = np.zeros(N, bool); order_used = np.zeros(N, int)
for i in range(N):
    hist = ((hist << 8) | int(text[i])) & ((1 << 48) - 1)           # context now ends at byte i; predict byte i+1
    best = None
    for k in reversed(range(len(ORDERS))):
        s, t = slot(k, hist); e = tables[k].get(s)
        if e and e[0] == t:
            best = (k, e[1]); break
    if best: pred[i] = best[1]; hit[i] = True; order_used[i] = ORDERS[best[0]]
    else: pred[i] = 32
    if i + 1 < N:                                                   # learn from the byte that actually followed (local update)
        nxt = int(text[i + 1])
        for k in range(len(ORDERS)):
            s, t = slot(k, hist); e = tables[k].get(s)
            if e and e[0] == t:
                if e[1] == nxt: e[2] = min(e[2] + 1, 3)
                elif e[2] > 0: e[2] -= 1
                else: e[1] = nxt
            else: tables[k][s] = [t, nxt, 0]
tt = text[1:]; p = pred[:-1]; b = big[:-1]; h = hit[:-1]; s_ = sp[:-1]
res = {"lookup_only": {"acc_true": float((p == tt).mean()), "agree_gpu": float((p == b).mean()), "coverage": float(h.mean()),
                       "acc_when_hit": float((p[h] == tt[h]).mean()), "acc_when_miss": float((p[~h] == tt[~h]).mean())},
       "spark_v2_full": {"acc_true": float((s_ == tt).mean()), "agree_gpu": float((s_ == b).mean())},
       "gpu_standin_model": {"acc_true": float((b == tt).mean())}}
M = len(tt); cuts = [1000, 2000, 5000, 10000, M]
res["learning_curve_lookup_acc"] = {str(c): float((p[:c] == tt[:c]).mean()) for c in cuts}
res["learning_curve_spark_acc"] = {str(c): float((s_[:c] == tt[:c]).mean()) for c in cuts}
print(json.dumps(res, indent=1))
json.dump(res, open(os.path.join(HERE, "..", "results", "matrix_free_probe.json"), "w"), indent=1)
