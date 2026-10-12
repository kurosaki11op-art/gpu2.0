"""Evaluate SPARK networks (trained on code or on prose) on the four held-out books, replace and hysteresis recall rules.
usage: python nontext_models.py <book dir> <model_dir>@H,D [...]      e.g. out_prose_64@64,32"""
import json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import nontext_probe as npb  # noqa
g1 = npb.g1
books_dir = sys.argv[1]; res = {}
for arg in sys.argv[2:]:
    name, _, hd = arg.partition("@")
    g1.H, g1.D = (int(x) for x in hd.split(",")) if hd else (128, 64)
    W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", name, "spark_v0_model.npz"))
    row = {"replace": [], "hyst": []}
    for b in npb.BOOKS:
        raw = np.frombuffer(open(os.path.join(books_dir, b), "rb").read(), dtype=np.uint8)
        s0 = int(len(raw) * 0.4); text = raw[s0:s0 + 20000]; tt = text[1:]
        for k, h in (("replace", False), ("hyst", True)):
            row[k].append(float((npb.spark(text, h, W)[:-1] == tt).mean()))
    res[arg] = {"replace_mean": float(np.mean(row["replace"])), "hyst_mean": float(np.mean(row["hyst"])), **row}
    print(arg, json.dumps({k: (round(v, 3) if isinstance(v, float) else [round(x, 3) for x in v]) for k, v in res[arg].items()}), flush=True)
json.dump(res, open(os.path.join(HERE, "..", "results", "nontext_models.json"), "w"), indent=1)
