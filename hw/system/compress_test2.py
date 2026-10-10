"""Idea A, round 2: SPARK as a context compressor at a FIXED GPU memory budget (LLMLingua-style evaluation).
For each target byte, the GPU model gets a context window of L bytes:
  plain      : the last L bytes
  spark      : the last K bytes verbatim + older bytes with SPARK-predictable ones (conf >= tau) removed, filling L
  random     : same as spark but removing the same fraction of bytes at random
  short      : only the last L*keep bytes (same compute as spark would need without compression)
Compare the GPU model's next-byte accuracy. If spark >= plain, SPARK lets a fixed context budget cover more history."""
import json, os, sys
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "train"), os.path.join(HERE, "third_party", "nanogpt")):
    sys.path.insert(0, p)
import train_spark_v0 as tr  # noqa
from model import GPT, GPTConfig  # noqa
import base64
t = json.load(open(os.path.join(HERE, "data", "spark_trace.json")))
text = np.frombuffer(base64.b64decode(t["text_b64"]), np.uint8).astype(np.int64)
conf = np.frombuffer(bytes.fromhex(t["conf_hex"]), np.uint8) / 255.0
ck = torch.load(os.path.join(HERE, "out_big", "gpu_model.pt")); m = GPT(GPTConfig(**ck["cfg"])); m.load_state_dict(ck["state"]); m.eval()
rng = np.random.default_rng(0)
pos = rng.choice(np.arange(3000, len(text) - 1), size=2500, replace=False)
K = 16


def ctx_for(i, L, mode, tau, keep_rate=None):
    recent = list(range(i - K + 1, i + 1))
    if mode == "plain":
        return list(range(i - L + 1, i + 1))
    if mode == "short":
        n = max(K, int(round(L * keep_rate)))
        return list(range(i - n + 1, i + 1))
    out, j = [], i - K
    while len(out) < L - K and j >= 0:
        # conf[j-1] is SPARK's confidence about byte j (predicting it from what came before)
        pred = conf[j - 1] >= tau if mode == "spark" else rng.random() < drop_rate
        if not pred:
            out.append(j)
        j -= 1
    return out[::-1] + recent


res = {}
for L in (64, 128):
    for tau in (0.9, 0.8):
        drop_rate = float(np.mean(conf[:-1] >= tau))
        accs = {}
        for mode in ("plain", "spark", "random", "short"):
            right = 0
            with torch.no_grad():
                for b in range(0, len(pos), 100):
                    batch = [ctx_for(i, L, mode, tau, keep_rate=1 - drop_rate) for i in pos[b:b + 100]]
                    ml = max(len(c) for c in batch)
                    for i, c in zip(pos[b:b + 100], batch):
                        lg, _ = m(torch.from_numpy(text[c])[None])
                        right += int(lg[0, -1].argmax()) == int(text[i + 1])
            accs[mode] = right / len(pos)
        res[f"L{L}_tau{tau}"] = {"drop_rate": drop_rate, **accs}
        print(f"context {L} bytes, SPARK removes {drop_rate:.0%} of older bytes (tau {tau}): "
              f"plain {accs['plain']:.1%} | SPARK-compressed {accs['spark']:.1%} | random removal {accs['random']:.1%} | "
              f"short window {accs['short']:.1%}", flush=True)
json.dump(res, open(os.path.join(HERE, "..", "results", "idea_a_compression_v2.json"), "w"), indent=1)
