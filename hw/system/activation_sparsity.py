#!/usr/bin/env python3
"""Brain principle 1: sparse, predictable activity. How much of a real LLM's MLP weight traffic could be skipped per token?

For every layer's MLP down-projection input a_t (one vector per token) we ask:
  oracle  : keep the k largest |a_t| (an upper bound; needs the activation first, so no saving by itself)
  prev    : predict the active set from the PREVIOUS token's active set (cheap, stateful)
  trace   : predict it from a leaky trace of past activity, score_t = decay*score_(t-1) + |a_(t-1)|
            (a leaky-integrator neuron per hidden unit: the same state a SPARK-style event-driven predictor can hold)
and measure the relative output error ||(a masked) W^T - a W^T|| / ||a W^T|| when only the predicted rows of W are read.
Weight bytes read are about the kept fraction f of that matrix. Real-model statistics only mean something with a real model.

Run on a real model (needs transformers + torch, GPU optional):
  py -3.12 hw\\system\\activation_sparsity.py --model Qwen/Qwen2.5-Coder-3B --n 8 --tokens 256
Plumbing test with a random tiny model (numbers meaningless):  python hw/system/activation_sparsity.py --tiny"""
import argparse, base64, json, os
import numpy as np, torch

HERE = os.path.dirname(os.path.abspath(__file__))
FRACS = (0.5, 0.3, 0.2, 0.1)


def topk_mask(score, k):
    idx = score.topk(k, dim=-1).indices
    m = torch.zeros_like(score, dtype=torch.bool); m.scatter_(-1, idx, True)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="Qwen/Qwen2.5-Coder-3B")
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--tokens", type=int, default=256)
    ap.add_argument("--decay", type=float, default=0.8)
    ap.add_argument("--tiny", action="store_true")
    a = ap.parse_args()
    from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    if a.tiny:
        from transformers import Qwen2Config, Qwen2ForCausalLM
        cfg = Qwen2Config(vocab_size=1000, hidden_size=64, intermediate_size=256, num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2)
        model = Qwen2ForCausalLM(cfg).eval(); tok = None
        ids_all = [torch.randint(0, 1000, (a.tokens,)) for _ in range(a.n)]
    else:
        tok = AutoTokenizer.from_pretrained(a.model)
        model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.float16 if dev == "cuda" else torch.float32).to(dev).eval()
        text = base64.b64decode(json.load(open(os.path.join(HERE, "data", "spark_trace.json")))["text_b64"]).decode("latin-1")
        enc = tok(text, return_tensors="pt").input_ids[0]
        starts = np.linspace(0, len(enc) - a.tokens - 1, a.n).astype(int)
        ids_all = [enc[s:s + a.tokens] for s in starts]
    acts = {}
    layers = model.model.layers
    hooks = [l.mlp.down_proj.register_forward_pre_hook(lambda m, i, li=li: acts.__setitem__(li, i[0].detach().float())) for li, l in enumerate(layers)]
    res = {f: {"oracle": [], "prev": [], "trace": []} for f in FRACS}
    with torch.no_grad():
        for ids in ids_all:
            model(ids[None].to(dev))
            for li, l in enumerate(layers):
                A = acts[li][0]                                   # [T, I]
                W = l.mlp.down_proj.weight.float()                # [H, I]
                dense = A @ W.t(); nd = dense.norm(dim=-1).clamp_min(1e-6)
                absA = A.abs(); T, I = absA.shape
                trace = torch.zeros_like(absA); s = torch.zeros(I, device=A.device)
                for t in range(T):                                # score used for token t comes from tokens < t only
                    trace[t] = s; s = a.decay * s + absA[t]
                for f in FRACS:
                    k = max(1, int(f * I))
                    for name, score in (("oracle", absA), ("prev", torch.cat([absA[:1] * 0, absA[:-1]])), ("trace", trace)):
                        m = topk_mask(score, k)
                        err = ((A * m) @ W.t() - dense).norm(dim=-1) / nd
                        res[f][name].append(err[8:].mean().item())
    for h in hooks:
        h.remove()
    out = {}
    print(f"mean relative output error of the MLP down-projection when only a fraction f of its inputs (weight columns) is read")
    print(f"{'f read':>7s} {'oracle':>8s} {'prev-token set':>15s} {'leaky trace':>12s}")
    for f in FRACS:
        r = {k: float(np.mean(v)) for k, v in res[f].items()}; out[str(f)] = r
        print(f"{f:7.0%} {r['oracle']:8.3f} {r['prev']:15.3f} {r['trace']:12.3f}")
    json.dump({"model": "tiny-random" if a.tiny else a.model, "decay": a.decay, "layers": len(layers), "result": out},
              open(os.path.join(HERE, "..", "results", "activation_sparsity%s.json" % ("_tiny" if a.tiny else "")), "w"), indent=1)


if __name__ == "__main__":
    main()
