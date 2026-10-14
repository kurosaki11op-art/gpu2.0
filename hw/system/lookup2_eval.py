"""Accuracy of the v2 lookup core (reference model) vs v1 on the 5 documents, and the 32-entry confidence table fitted on the
calibration streams (first 100k bytes of the code and prose training corpora). Writes hw/rtl/lookup/conf_lut.hex.
usage: python lookup2_eval.py <book dir> <prose_train.txt>"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "train")):
    sys.path.insert(0, p)
from lookup_ref import LookupCore, LookupCoreV2  # noqa
import train_spark_v0 as tr  # noqa


def run(core, data):
    rows = [core.step(b) for b in data]; t = np.frombuffer(bytes(data), dtype=np.uint8)
    return np.array([r[0] for r in rows])[:-1] == t[1:], np.array([r[4] if len(r) > 4 else 0 for r in rows])[:-1]


cal_ok, cal_b = [], []
for data in (bytes(tr.load_corpus(100000)), open(sys.argv[2], "rb").read()[:100000]):
    o, b = run(LookupCoreV2(11), data); cal_ok.append(o); cal_b.append(b)
cal_ok, cal_b = np.concatenate(cal_ok), np.concatenate(cal_b)
lut = [int(round(255 * (cal_ok[cal_b == k].mean() if (cal_b == k).sum() >= 20 else cal_ok.mean()))) for k in range(32)]
open(os.path.join(HERE, "..", "rtl", "lookup", "conf_lut.hex"), "w").write("\n".join("%02x" % v for v in lut) + "\n")
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz")); docs = {"code": bytes(Z["test_text"])}
for bk in ("carroll-alice.txt", "melville-moby_dick.txt", "shakespeare-hamlet.txt", "austen-emma.txt"):
    raw = open(os.path.join(sys.argv[1], bk), "rb").read(); s0 = int(len(raw) * 0.4); docs[bk.split(".")[0]] = raw[s0:s0 + 20000]
res = {"lut": lut, "docs": {}}
for name, data in docs.items():
    a1 = run(LookupCore(12), data)[0].mean(); o2, b2 = run(LookupCoreV2(11), data)
    conf = np.array(lut)[b2] / 255.0; top = conf >= 0.9
    res["docs"][name] = {"v1_46KB": float(a1), "v2_49KB": float(o2.mean()), "v2_conf_ge_0.9_share": float(top.mean()),
                         "v2_acc_conf_ge_0.9": float(o2[top].mean()) if top.any() else None}
    print(name, {k: round(v, 4) if isinstance(v, float) else v for k, v in res["docs"][name].items()}, flush=True)
print("LUT %:", " ".join(f"{v / 2.55:.0f}" for v in lut[:21]))
json.dump(res, open(os.path.join(HERE, "..", "results", "lookup2_eval.json"), "w"), indent=1)
