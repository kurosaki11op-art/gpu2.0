#!/usr/bin/env python3
"""Test B: batch-1 decode speed against the weights-only memory floor, eager versus CUDA graphs (static cache + torch.compile reduce-overhead).
usage: python graphs_test.py MODEL_ID [--out graphs_MODEL.json] [--new 128] [--prompt 256]
Reports for each mode: ms per token, tokens per second, fraction of the weights-only floor (weight bytes / measured copy bandwidth). If a mode fails (for example compile is not available on Windows) the error is recorded and the next mode runs.
For a serving engine with graphs on by default (Colab T4, Linux): pip install vllm, then see the comment at the end of this file."""
import argparse, json, time, torch
from transformers import AutoModelForCausalLM

ap = argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("--out", default="graphs_result.json"); ap.add_argument("--new", type=int, default=128); ap.add_argument("--prompt", type=int, default=256)
a = ap.parse_args(); assert torch.cuda.is_available(), "this test needs a CUDA GPU"
def bw():
    n = 256 * 1024 * 1024 // 2; x = torch.empty(n, dtype=torch.float16, device="cuda"); y = torch.empty_like(x); torch.cuda.synchronize()
    for _ in range(3): y.copy_(x)
    torch.cuda.synchronize(); t = time.time()
    for _ in range(20): y.copy_(x)
    torch.cuda.synchronize(); return 2 * x.numel() * 2 * 20 / (time.time() - t) / 1e9
res = {"gpu": torch.cuda.get_device_name(0), "model": a.model, "torch": torch.__version__, "copy_bandwidth_gbs": bw(), "runs": []}
def load(): 
    try: m = AutoModelForCausalLM.from_pretrained(a.model, dtype=torch.float16)
    except TypeError: m = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.float16)
    return m.cuda().eval()
def timed(model, gen_kwargs):
    ids = torch.randint(0, model.config.vocab_size, (1, a.prompt), device="cuda"); att = torch.ones_like(ids)
    kw = dict(attention_mask=att, do_sample=False, pad_token_id=0, **gen_kwargs)
    with torch.no_grad():
        for _ in range(3): model.generate(ids, max_new_tokens=8, min_new_tokens=8, **kw)  # warm-up (compiles and captures graphs)
        torch.cuda.synchronize(); t = time.time(); out = model.generate(ids, max_new_tokens=a.new, min_new_tokens=a.new, **kw); torch.cuda.synchronize(); dt = time.time() - t
    return dt / (out.shape[1] - a.prompt)
for mode in ["eager", "static_compile_graphs"]:
    r = {"mode": mode}
    try:
        model = load(); wb = sum(p.numel() * p.element_size() for p in model.parameters()); res["weight_bytes"] = wb
        if mode == "eager": t = timed(model, {})
        else:
            model.forward = torch.compile(model.forward, mode="reduce-overhead", fullgraph=True); t = timed(model, {"cache_implementation": "static"})
        floor = wb / (res["copy_bandwidth_gbs"] * 1e9); r.update({"ms_per_token": t * 1e3, "tokens_per_s": 1 / t, "floor_ms": floor * 1e3, "fraction_of_floor": floor / t})
    except Exception as e:
        r["error"] = "%s: %s" % (type(e).__name__, str(e)[:300])
    print(r); res["runs"].append(r); del model; torch.cuda.empty_cache()
json.dump(res, open(a.out, "w"), indent=1); print("written", a.out)
# vLLM on Linux (Colab T4): in a notebook, !pip -q install vllm, then
#   from vllm import LLM, SamplingParams; import time
#   llm = LLM(MODEL, dtype="float16", max_model_len=1024); sp = SamplingParams(max_tokens=128, min_tokens=128, temperature=0)
#   llm.generate(["hello"]*1, sp); t=time.time(); llm.generate(["word "*250], sp); dt=(time.time()-t)/128   # seconds per token at batch 1
# then fraction_of_floor = (weight_bytes / (copy_bandwidth_gbs*1e9)) / dt. Graphs are on by default in vLLM (enforce_eager=False).
