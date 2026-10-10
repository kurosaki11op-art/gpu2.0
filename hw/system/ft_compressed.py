"""Idea A, round 3: adapt the GPU model to SPARK-compressed context.
Fine-tune the trained GPU model (out_big) for --steps on 128-byte contexts that are either
  plain    : the last 128 bytes, or
  spark    : the last 16 bytes verbatim + older bytes with SPARK conf >= tau removed (reaches further back).
Loss only on the verbatim last 16 positions (their true next byte). Then evaluate both on held-out text with the
same kind of context they were trained on, and on plain context. Equal extra training = fair comparison."""
import argparse, json, os, sys, base64
import numpy as np, torch, torch.nn.functional as F
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, "..", "train"), os.path.join(HERE, "third_party", "nanogpt")):
    sys.path.insert(0, p)
import train_spark_v0 as tr  # noqa
from model import GPT, GPTConfig  # noqa
ap = argparse.ArgumentParser(); ap.add_argument("--mode", required=True, choices=["plain", "spark"])
ap.add_argument("--steps", type=int, default=800); ap.add_argument("--tau", type=float, default=0.9)
ap.add_argument("--threads", type=int, default=1); a = ap.parse_args()
torch.set_num_threads(a.threads); torch.manual_seed(0); rng = np.random.default_rng(0)
L, K = 128, 16
data = tr.load_corpus(3_000_000); train = data[: int(len(data) * 0.9)].astype(np.int64)
tconf = np.load(os.path.join(HERE, "out", "train_conf.npy")) / 255.0
t = json.load(open(os.path.join(HERE, "data", "spark_trace.json")))
test = np.frombuffer(base64.b64decode(t["text_b64"]), np.uint8).astype(np.int64)
xconf = np.frombuffer(bytes.fromhex(t["conf_hex"]), np.uint8) / 255.0


def ctx(seq, conf, i, mode):
    """context indices ending at i (inclusive) plus verbatim recent block"""
    if mode == "plain":
        return list(range(i - L + 1, i + 1))
    out, j = [], i - K
    while len(out) < L - K and j > 0:
        if conf[j - 1] < a.tau:
            out.append(j)
        j -= 1
    while len(out) < L - K:
        out.append(0)
    return out[::-1] + list(range(i - K + 1, i + 1))


ck = torch.load(os.path.join(HERE, "out_big", "gpu_model.pt")); m = GPT(GPTConfig(**ck["cfg"])); m.load_state_dict(ck["state"])
opt = torch.optim.AdamW(m.parameters(), lr=2e-4)
for step in range(a.steps):
    ii = rng.integers(20000, len(train) - 2, size=32)
    x = torch.from_numpy(np.stack([train[ctx(train, tconf, i, a.mode)] for i in ii]))
    y = torch.from_numpy(np.stack([train[np.arange(i - K + 2, i + 2)] for i in ii]))
    lg, _ = m(x, targets=x)
    loss = F.cross_entropy(lg[:, -K:].reshape(-1, 256), y.reshape(-1))
    opt.zero_grad(); loss.backward(); opt.step()
    if step % 100 == 0:
        print(f"{a.mode} step {step} loss {loss.item():.3f}", flush=True)
m.eval()
pos = np.random.default_rng(1).choice(np.arange(3000, len(test) - 1), size=2000, replace=False)
res = {}
with torch.no_grad():
    for ev in ("plain", "spark"):
        right = 0
        for b in range(0, len(pos), 100):
            xb = torch.from_numpy(np.stack([test[ctx(test, xconf, i, ev)] for i in pos[b:b + 100]]))
            lg, _ = m(xb)
            right += int(np.sum(lg[:, -1].argmax(-1).numpy() == test[pos[b:b + 100] + 1]))
        res[ev] = right / len(pos)
print(f"RESULT fine-tuned on {a.mode}: accuracy with plain context {res['plain']:.1%}, with SPARK-compressed context {res['spark']:.1%}", flush=True)
json.dump(res, open(os.path.join(HERE, "..", "results", f"idea_a_ft_{a.mode}.json"), "w"))
