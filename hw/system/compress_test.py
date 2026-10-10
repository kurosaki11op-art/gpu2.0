"""Idea A: SPARK as a hardware prompt compressor for long inputs (chip design unchanged).
SPARK reads the input; bytes it is confident about (calibrated conf >= tau) are 'predictable'. If they carry little
information for the big model, the GPU can drop or summarise them (fewer tokens in attention and the KV cache).
Measure: share of the GPU model's information (its negative log-likelihood, bits) that sits in SPARK-confident bytes,
and how much input remains at each threshold. Attention cost ~ length^2, KV memory ~ length."""
import json, os, sys
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "golden")); sys.path.insert(0, os.path.join(HERE, "..", "train"))
sys.path.insert(0, os.path.join(HERE, "third_party", "nanogpt"))
import spark_golden as g1, spark_golden_v2 as g2, train_spark_v0 as tr  # noqa
from model import GPT, GPTConfig  # noqa

data = tr.load_corpus(3_000_000); n = len(data)
test = data[int(n * 0.95): int(n * 0.95) + 20000]
W = g1.Weights.from_npz(os.path.join(HERE, "..", "train", "out_qat_sp0.05", "spark_v0_model.npz"))
lut = json.load(open(os.path.join(HERE, "..", "results", "rlcd_results.json")))["lut_rlcd_8bit"]
g = g2.GoldenV2(W, g1.Cfg(a=230, acc_sh=2, s_sh=4, spike_mode="thr", recall=1, conf_th=0, recall_mode=0, exit_en=1, exit_th=16), tb=12, lut=lut)
conf = np.array([g.step(int(b))["conf"] for b in test]) / 255.0       # conf[i]: SPARK's confidence about byte i+1

ck = torch.load(os.path.join(HERE, "out_big", "gpu_model.pt")); m = GPT(GPTConfig(**ck["cfg"])); m.load_state_dict(ck["state"]); m.eval()
x = torch.from_numpy(test.astype(np.int64)); nll = np.zeros(len(test))
with torch.no_grad():
    for s in range(0, len(test), 64):
        lo = max(0, s - 64); hi = min(len(test), s + 64)
        lg, _ = m(x[lo:hi][None], targets=x[lo:hi][None])
        lp = torch.log_softmax(lg[0], -1)
        for i in range(s, hi - 1):
            nll[i] = -lp[i - lo, test[i + 1]].item() / np.log(2)     # bits the GPU model needs for byte i+1
nll = nll[:-1]; conf = conf[:-1]
tot = nll.sum()
print(f"GPU model information in the text: {tot/len(nll):.2f} bits/byte")
out = []
for tau in (0.6, 0.7, 0.8, 0.9, 0.95):
    keep = conf < tau
    kept_frac = keep.mean()
    info_dropped = nll[~keep].sum() / tot
    attn = kept_frac ** 2
    out.append(dict(tau=tau, input_kept=float(kept_frac), info_in_dropped=float(info_dropped),
                    bits_per_dropped_byte=float(nll[~keep].mean()) if (~keep).any() else 0,
                    bits_per_kept_byte=float(nll[keep].mean()), attention_cost=float(attn), kv_memory=float(kept_frac)))
    print(f"tau {tau}: drop {1-kept_frac:5.1%} of bytes, they hold {info_dropped:5.1%} of the information "
          f"({nll[~keep].mean():.2f} vs {nll[keep].mean():.2f} bits/byte kept) -> attention {attn:5.1%}, KV memory {kept_frac:5.1%}")
# random baseline at the same drop rate
r = np.random.default_rng(0).permutation(len(nll))
for o in out:
    k = int((1 - o["input_kept"]) * len(nll)); o["random_info_dropped"] = float(nll[r[:k]].sum() / tot)
print("random dropping at the same rates removes:", ", ".join(f"{o['random_info_dropped']:.1%}" for o in out))
json.dump({"bits_per_byte": float(tot / len(nll)), "points": out}, open(os.path.join(HERE, "..", "results", "idea_a_compression.json"), "w"), indent=1)
