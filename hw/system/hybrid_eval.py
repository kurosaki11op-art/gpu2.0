"""Hybrid SPARK (recall tables + 64/32 network) on code and prose. Early exit off (exit head unused), hysteresis recall update.
usage: python hybrid_eval.py <book dir> <model_dir> [<model_dir> ...]     (all 64/32)
Code: 20,000 held-out bytes (accuracy vs true byte, agreement with the GPU stand-in). Prose: the four book slices (accuracy)."""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nontext_probe as npb  # noqa
g1 = npb.g1; g1.H, g1.D = 64, 32
Z = np.load(os.path.join(HERE, "out", "slice_cache.npz")); code, big = Z["test_text"], Z["test_big_pred"]
npb.CFG["exit_en"] = 0
res = {}
for name in sys.argv[2:]:
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", name, "spark_v0_model.npz"))
    p = npb.spark(code, True, W)[:-1]
    row = {"code_acc": float((p == code[1:]).mean()), "code_agree_gpu": float((p == big[:-1]).mean()), "prose": []}
    for b in npb.BOOKS:
        raw = np.frombuffer(open(os.path.join(sys.argv[1], b), "rb").read(), dtype=np.uint8)
        s0 = int(len(raw) * 0.4); t = raw[s0:s0 + 20000]
        row["prose"].append(float((npb.spark(t, True, W)[:-1] == t[1:]).mean()))
    row["prose_mean"] = float(np.mean(row["prose"])); res[name] = row
    print(name, json.dumps({k: (round(v, 4) if isinstance(v, float) else [round(x, 3) for x in v]) for k, v in row.items()}), flush=True)
json.dump(res, open(os.path.join(HERE, "..", "results", "hybrid_eval.json"), "w"), indent=1)
