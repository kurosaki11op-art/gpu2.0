"""Accuracy and bits/byte of a GPU-side checkpoint on the held-out test slice (idea C comparison)."""
import json, os, sys
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "train"), os.path.join(HERE, "third_party", "nanogpt")):
    sys.path.insert(0, p)
import train_spark_v0 as tr  # noqa
from model import GPT, GPTConfig  # noqa
data = tr.load_corpus(3_000_000); n = len(data); test = data[int(n * 0.95): int(n * 0.95) + 20000]
x = torch.from_numpy(test.astype(np.int64))
res = {}
for path in sys.argv[1:]:
    ck = torch.load(path); m = GPT(GPTConfig(**ck["cfg"])); m.load_state_dict(ck["state"]); m.eval()
    right = bits = cnt = 0
    with torch.no_grad():
        for s in range(0, len(test), 64):
            lo = max(0, s - 64); hi = min(len(test), s + 64)
            lg, _ = m(x[lo:hi][None], targets=x[lo:hi][None]); lp = torch.log_softmax(lg[0], -1)
            for i in range(s, hi - 1):
                right += int(lp[i - lo].argmax()) == int(test[i + 1]); bits += -lp[i - lo, test[i + 1]].item() / np.log(2); cnt += 1
    res[path] = {"accuracy": right / cnt, "bits_per_byte": bits / cnt}
    print(f"{path}: accuracy {right/cnt:.1%}, {bits/cnt:.3f} bits/byte", flush=True)
json.dump(res, open(os.path.join(HERE, "..", "results", "idea_c_training_filter.json"), "w"), indent=1)
