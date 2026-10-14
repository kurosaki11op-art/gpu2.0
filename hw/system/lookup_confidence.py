"""Calibrated confidence for the lookup core with no arithmetic beyond counting: a 17-entry table indexed by
(which table answered: order 2/3/4/6) x (its 2-bit counter), plus one entry for "no table answered".
Fit on calibration streams (training corpora, first 100k bytes of code and of prose), tested on the held-out documents.
Reports per-bucket accuracy, expected calibration error (ECE), and whether confidence ranks right from wrong (AUC).
usage: python lookup_confidence.py <book dir> <prose_train.txt>"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "train")):
    sys.path.insert(0, p)
from lookup_ref import LookupCore  # noqa
import train_spark_v0 as tr  # noqa


def run(data):
    c = LookupCore(12); rows = [c.step(b) for b in data]
    pred = np.array([r[0] for r in rows]); bucket = np.array([r[2] * 4 + r[3] if r[1] else 16 for r in rows])
    return pred[:-1] == np.frombuffer(bytes(data), dtype=np.uint8)[1:], bucket[:-1]


cal_ok, cal_b = [], []
for data in (bytes(tr.load_corpus(100000)), open(sys.argv[2], "rb").read()[:100000]):
    o, b = run(data); cal_ok.append(o); cal_b.append(b)
cal_ok, cal_b = np.concatenate(cal_ok), np.concatenate(cal_b)
lut = np.array([cal_ok[cal_b == k].mean() if (cal_b == k).sum() >= 20 else cal_ok.mean() for k in range(17)])
lut8 = np.round(lut * 255).astype(int)
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz")); docs = {"code": bytes(Z["test_text"])}
for bk in ("carroll-alice.txt", "melville-moby_dick.txt", "shakespeare-hamlet.txt", "austen-emma.txt"):
    raw = open(os.path.join(sys.argv[1], bk), "rb").read(); s0 = int(len(raw) * 0.4); docs[bk.split(".")[0]] = raw[s0:s0 + 20000]
res = {"lut_8bit": lut8.tolist(), "buckets": "order_idx*4 + count (orders 2,3,4,6), 16 = no table answered", "docs": {}}
for name, data in docs.items():
    ok, b = run(data); conf = lut8[b] / 255.0
    bins = np.clip((conf * 10).astype(int), 0, 9)
    ece = sum(abs(ok[bins == i].mean() - conf[bins == i].mean()) * (bins == i).mean() for i in range(10) if (bins == i).any())
    pos, neg = conf[ok], conf[~ok]
    auc = float(np.mean([(pos[:, None] > neg[None, :]).mean() + 0.5 * (pos[:, None] == neg[None, :]).mean()])) if len(pos) * len(neg) < 4e8 else None
    top = conf >= 0.9
    res["docs"][name] = {"acc": float(ok.mean()), "ece": float(ece), "auc": auc, "share_conf_ge_0.9": float(top.mean()),
                         "acc_when_conf_ge_0.9": float(ok[top].mean()) if top.any() else None}
    print(name, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res["docs"][name].items()}, flush=True)
print("LUT (per bucket, %):", " ".join(f"{v / 2.55:.0f}" for v in lut8))
json.dump(res, open(os.path.join(HERE, "..", "results", "lookup_confidence.json"), "w"), indent=1)
