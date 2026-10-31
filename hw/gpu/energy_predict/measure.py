#!/usr/bin/env python3
"""Energy-per-token measurement for one GPU (wedge 1, test G1). Run this on the machine being measured. Needs: python 3, torch with CUDA, transformers, nvidia-smi.
usage: python measure.py MODEL_ID_OR_PATH [--batches 1 4 16] [--prompt 256] [--new 128] [--out results.json]
Steps: (1) measures memory bandwidth with a copy test, (2) idle power for 30 s, (3) for each batch size decodes `new` tokens from a `prompt`-token input while sampling board power every 0.1 s, (4) writes everything to JSON.
It prints N/A for power if nvidia-smi does not report it (some laptops); the speed numbers are still valid.
Close other programs first. Plug the laptop into mains and set the same power mode for every run. Do not touch the machine during a run."""
import argparse, json, subprocess, threading, time
import torch
from transformers import AutoModelForCausalLM

def smi(q):
    try:
        v = subprocess.check_output(["nvidia-smi", "--query-gpu=" + q, "--format=csv,noheader,nounits"], text=True).strip().split("\n")[0]
        return float(v)
    except Exception:
        return None

class Sampler(threading.Thread):
    def __init__(s): super().__init__(daemon=True); s.v = []; s.run_flag = True
    def run(s):
        while s.run_flag:
            p = smi("power.draw")
            if p is not None: s.v.append(p)
            time.sleep(0.1)

def bandwidth_gbs():
    n = 256 * 1024 * 1024 // 2  # 256 MB of fp16
    a = torch.empty(n, dtype=torch.float16, device="cuda"); b = torch.empty_like(a); torch.cuda.synchronize()
    for _ in range(3): b.copy_(a)
    torch.cuda.synchronize(); t = time.time(); k = 20
    for _ in range(k): b.copy_(a)
    torch.cuda.synchronize(); dt = time.time() - t
    return 2 * a.numel() * 2 * k / dt / 1e9  # read + write bytes

ap = argparse.ArgumentParser(); ap.add_argument("model"); ap.add_argument("--batches", type=int, nargs="+", default=[1, 4, 16])
ap.add_argument("--prompt", type=int, default=256); ap.add_argument("--new", type=int, default=128); ap.add_argument("--out", default="results.json"); ap.add_argument("--info-only", action="store_true", help="measure only the GPU name, copy bandwidth and idle power, then stop")
a = ap.parse_args()
dev = torch.cuda.get_device_properties(0)
res = {"gpu": dev.name, "vram_gb": dev.total_memory / 1e9, "torch": torch.__version__, "model": a.model, "prompt": a.prompt, "new": a.new, "runs": []}
res["bandwidth_copy_gbs"] = bandwidth_gbs()
print("GPU", dev.name, "copy bandwidth GB/s", round(res["bandwidth_copy_gbs"], 1))
smp = Sampler(); smp.start(); time.sleep(30); idle = smp.v[:]; smp.v = []
res["idle_power_w"] = sum(idle) / len(idle) if idle else None; print("idle power W", res["idle_power_w"])
if a.info_only:
    smp.run_flag = False; json.dump(res, open(a.out, "w"), indent=1); print("info written", a.out, "(send this file; no model was run)"); raise SystemExit
model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.float16).cuda().eval()
res["weight_bytes"] = sum(p.numel() * p.element_size() for p in model.parameters())
cfg = model.config; res["layers"] = getattr(cfg, "num_hidden_layers", None); res["hidden"] = getattr(cfg, "hidden_size", None)
res["kv_heads"] = getattr(cfg, "num_key_value_heads", getattr(cfg, "num_attention_heads", None)); res["heads"] = getattr(cfg, "num_attention_heads", None)
vocab = cfg.vocab_size
for B in a.batches:
    try:
        ids = torch.randint(0, vocab, (B, a.prompt), device="cuda")
        with torch.no_grad():
            model.generate(ids, max_new_tokens=4, do_sample=False, min_new_tokens=4)  # warm-up
            torch.cuda.synchronize(); smp.v = []; time.sleep(1.0); smp.v = []
            t0 = time.time(); out = model.generate(ids, max_new_tokens=a.new, min_new_tokens=a.new, do_sample=False); torch.cuda.synchronize(); t1 = time.time()
        pw = list(smp.v); gen = out.shape[1] - a.prompt
        r = {"batch": B, "seconds": t1 - t0, "new_tokens": gen, "tokens_per_s_total": B * gen / (t1 - t0), "tokens_per_s_per_user": gen / (t1 - t0),
             "mean_power_w": sum(pw) / len(pw) if pw else None, "peak_mem_gb": torch.cuda.max_memory_allocated() / 1e9}
        if r["mean_power_w"] is not None:
            r["joules_per_token_gross"] = r["mean_power_w"] * (t1 - t0) / (B * gen)
            if res["idle_power_w"] is not None: r["joules_per_token_net"] = (r["mean_power_w"] - res["idle_power_w"]) * (t1 - t0) / (B * gen)
        else: r["note"] = "power N/A"
        print(r); res["runs"].append(r)
    except torch.cuda.OutOfMemoryError:
        print("batch", B, "out of memory"); res["runs"].append({"batch": B, "error": "out of memory"}); torch.cuda.empty_cache()
smp.run_flag = False
json.dump(res, open(a.out, "w"), indent=1); print("written", a.out)
